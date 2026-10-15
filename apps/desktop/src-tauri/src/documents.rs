//! Fixed-root export of approved Core documents; renderer supplies no path or file content.
use crate::bridge::{Bridge, CoreRequest};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::{
    collections::BTreeMap,
    fs,
    io::Write,
    path::{Path, PathBuf},
    sync::atomic::{AtomicU64, Ordering},
};
use tauri::{AppHandle, Manager, State};

const NAMES: [&str; 9] = [
    "01_PRODUCT_REQUIREMENTS.md",
    "02_SYSTEM_ARCHITECTURE.md",
    "03_DEVELOPMENT_RULES.md",
    "04_DESIGN_SYSTEM.md",
    "05_PROJECT_TASKS.md",
    "06_PROJECT_MEMORY.md",
    "07_API_AND_EVENTS.md",
    "08_TESTING_AND_ACCEPTANCE.md",
    "09_SECURITY_AND_OPERATIONS.md",
];
static NEXT: AtomicU64 = AtomicU64::new(0);

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Prepared {
    id: String,
    project: String,
    version: u64,
    sha256: String,
    canonical_documents: String,
    approved: f64,
    prepared: f64,
    parent_spec: Option<String>,
}
#[derive(Serialize)]
pub struct Exported {
    directory: String,
    files: usize,
    existing: bool,
}
fn fail(_: impl std::fmt::Debug) -> String {
    "Document export unavailable; existing files were not overwritten.".into()
}
fn hex(value: &str, size: usize) -> bool {
    value.len() == size
        && value
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}
fn validate(data: &Prepared) -> Result<BTreeMap<String, String>, String> {
    if !hex(&data.id, 32)
        || !hex(&data.project, 32)
        || !hex(&data.sha256, 64)
        || data.version == 0
        || data.parent_spec.as_ref().is_some_and(|id| !hex(id, 32))
        || data.approved < 0.0
        || data.prepared < data.approved
        || !data.approved.is_finite()
        || !data.prepared.is_finite()
        || data.canonical_documents.len() > 64000
        || format!("{:x}", Sha256::digest(data.canonical_documents.as_bytes())) != data.sha256
    {
        return Err(fail(()));
    }
    let docs: BTreeMap<String, String> =
        serde_json::from_str(&data.canonical_documents).map_err(fail)?;
    if docs.len() < 4
        || docs.len() > 9
        || [0, 4, 5, 7].iter().any(|i| !docs.contains_key(NAMES[*i]))
        || docs.iter().any(|(name, text)| {
            !NAMES.contains(&name.as_str())
                || text.trim().is_empty()
                || text.contains('\0')
                || text.len() > 24000
        })
    {
        return Err(fail(()));
    }
    Ok(docs)
}
fn plain_directory(path: &Path) -> Result<(), String> {
    match fs::create_dir(path) {
        Ok(()) => (),
        Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => (),
        Err(e) => return Err(fail(e)),
    }
    let metadata = fs::symlink_metadata(path).map_err(fail)?;
    #[cfg(windows)]
    {
        use std::os::windows::fs::MetadataExt;
        if metadata.file_attributes() & 0x400 != 0 {
            return Err(fail(()));
        }
    }
    if !metadata.is_dir() || metadata.file_type().is_symlink() {
        return Err(fail(()));
    }
    Ok(())
}
fn read_plain(path: &Path) -> Result<Vec<u8>, String> {
    let metadata = fs::symlink_metadata(path).map_err(fail)?;
    #[cfg(windows)]
    {
        use std::os::windows::fs::MetadataExt;
        if metadata.file_attributes() & 0x400 != 0 {
            return Err(fail(()));
        }
    }
    if !metadata.is_file() || metadata.file_type().is_symlink() || metadata.len() > 262144 {
        return Err(fail(()));
    }
    fs::read(path).map_err(fail)
}
fn existing(path: &Path, data: &Prepared, docs: &BTreeMap<String, String>) -> Result<(), String> {
    plain_directory(path)?;
    let manifest: Prepared =
        serde_json::from_slice(&read_plain(&path.join("manifest.json"))?).map_err(fail)?;
    validate(&manifest)?;
    if manifest.id != data.id
        || manifest.project != data.project
        || manifest.version != data.version
        || manifest.parent_spec != data.parent_spec
        || manifest.approved != data.approved
        || manifest.prepared > data.prepared
        || manifest.sha256 != data.sha256
        || manifest.canonical_documents != data.canonical_documents
        || fs::read_dir(path).map_err(fail)?.count() != docs.len() + 1
    {
        return Err(fail(()));
    }
    for (name, text) in docs {
        if read_plain(&path.join(name))? != text.as_bytes() {
            return Err(fail(()));
        }
    }
    Ok(())
}
fn write_new(path: &Path, bytes: &[u8]) -> Result<(), String> {
    let mut file = fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .map_err(fail)?;
    file.write_all(bytes).map_err(fail)?;
    file.sync_all().map_err(fail)
}
fn export(root: &Path, data: &Prepared) -> Result<Exported, String> {
    let docs = validate(data)?;
    plain_directory(root)?;
    let project = root.join(&data.project);
    plain_directory(&project)?;
    let final_path = project.join(format!("v{}-{}", data.version, data.id));
    if final_path.try_exists().map_err(fail)? {
        existing(&final_path, data, &docs)?;
        return Ok(Exported {
            directory: final_path.to_string_lossy().into(),
            files: docs.len(),
            existing: true,
        });
    }
    let staging = project.join(format!(
        ".pending-{}-{}-{}",
        data.id,
        std::process::id(),
        NEXT.fetch_add(1, Ordering::Relaxed)
    ));
    fs::create_dir(&staging).map_err(fail)?;
    let result = (|| {
        for (name, text) in &docs {
            write_new(&staging.join(name), text.as_bytes())?;
        }
        write_new(
            &staging.join("manifest.json"),
            &serde_json::to_vec_pretty(data).map_err(fail)?,
        )?;
        fs::rename(&staging, &final_path).map_err(fail)?;
        Ok(Exported {
            directory: final_path.to_string_lossy().into(),
            files: docs.len(),
            existing: false,
        })
    })();
    if result.is_err() {
        // Remove only known files in this call's newly created staging folder, never recurse.
        for name in NAMES
            .iter()
            .copied()
            .chain(std::iter::once("manifest.json"))
        {
            let _ = fs::remove_file(staging.join(name));
        }
        let _ = fs::remove_dir(&staging);
    }
    result
}
fn root(app: &AppHandle) -> Result<PathBuf, String> {
    if let Some(value) = std::env::var_os("JARVIS_EXPORT_ROOT") {
        let path = PathBuf::from(value);
        if !path.is_absolute() {
            return Err(fail(()));
        }
        // Explicit trusted host configuration; parent must already exist.
        return Ok(path);
    }
    let mut path = app.path().document_dir().map_err(fail)?;
    for name in ["Skyra", "Jarvis", "exports"] {
        path.push(name);
        plain_directory(&path)?;
    }
    Ok(path)
}
#[tauri::command]
pub async fn export_specification(
    app: AppHandle,
    state: State<'_, Bridge>,
    id: String,
    expected_sha256: String,
) -> Result<Exported, String> {
    if !hex(&id, 32) || !hex(&expected_sha256, 64) {
        return Err(fail(()));
    }
    let value = state
        .dispatch(CoreRequest::specification_export(
            id.clone(),
            expected_sha256.clone(),
        ))
        .await
        .map_err(fail)?;
    let data: Prepared = serde_json::from_value(value).map_err(fail)?;
    if data.id != id || data.sha256 != expected_sha256 {
        return Err(fail(()));
    }
    export(&root(&app)?, &data)
}

#[cfg(test)]
mod tests {
    use super::*;
    fn prepared() -> Prepared {
        let docs: BTreeMap<_, _> = [0, 4, 5, 7]
            .iter()
            .map(|i| (NAMES[*i].to_string(), "# Owner reviewed\n".to_string()))
            .collect();
        let canonical_documents = serde_json::to_string(&docs).unwrap();
        Prepared {
            id: "a".repeat(32),
            project: "b".repeat(32),
            version: 1,
            sha256: format!("{:x}", Sha256::digest(canonical_documents.as_bytes())),
            canonical_documents,
            approved: 1.0,
            prepared: 2.0,
            parent_spec: None,
        }
    }
    #[test]
    fn writes_exact_files_and_rejects_tampered_reexport() {
        let root = std::env::temp_dir().join(format!(
            "jarvis-docs-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        let data = prepared();
        let first = export(&root, &data).unwrap();
        assert!(!first.existing);
        assert!(export(&root, &data).unwrap().existing);
        let output = PathBuf::from(first.directory);
        fs::write(output.join(NAMES[0]), "Owner edited externally").unwrap();
        assert!(export(&root, &data).is_err());
        assert_eq!(
            fs::read_to_string(output.join(NAMES[0])).unwrap(),
            "Owner edited externally"
        );
        for name in [NAMES[0], NAMES[4], NAMES[5], NAMES[7], "manifest.json"] {
            fs::remove_file(output.join(name)).unwrap();
        }
        fs::remove_dir(&output).unwrap();
        fs::remove_dir(root.join(&data.project)).unwrap();
        fs::remove_dir(root).unwrap();
    }
    #[test]
    fn maximum_escaped_manifest_reexports_and_checks_provenance() {
        let root = std::env::temp_dir().join(format!(
            "jarvis-docs-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        let mut data = prepared();
        let mut docs = validate(&data).unwrap();
        for text in docs.values_mut() {
            *text = "\"".repeat(7980);
        }
        data.canonical_documents = serde_json::to_string(&docs).unwrap();
        data.sha256 = format!("{:x}", Sha256::digest(data.canonical_documents.as_bytes()));
        assert!(data.canonical_documents.len() <= 64000);
        let output = PathBuf::from(export(&root, &data).unwrap().directory);
        assert!(fs::metadata(output.join("manifest.json")).unwrap().len() > 128000);
        assert!(export(&root, &data).unwrap().existing);
        let mut altered = serde_json::to_value(&data).unwrap();
        altered["parent_spec"] = serde_json::json!("f".repeat(32));
        fs::write(
            output.join("manifest.json"),
            serde_json::to_vec(&altered).unwrap(),
        )
        .unwrap();
        assert!(export(&root, &data).is_err());
        for name in [NAMES[0], NAMES[4], NAMES[5], NAMES[7], "manifest.json"] {
            fs::remove_file(output.join(name)).unwrap();
        }
        fs::remove_dir(output).unwrap();
        fs::remove_dir(root.join(&data.project)).unwrap();
        fs::remove_dir(root).unwrap();
    }

    #[test]
    fn rejects_bad_checksum_paths_and_document_names() {
        let mut data = prepared();
        data.project = "../escape".into();
        assert!(validate(&data).is_err());
        let mut data = prepared();
        data.sha256 = "0".repeat(64);
        assert!(validate(&data).is_err());
        let mut data = prepared();
        let mut docs = validate(&data).unwrap();
        docs.insert("../evil.md".into(), "evil".into());
        data.canonical_documents = serde_json::to_string(&docs).unwrap();
        data.sha256 = format!("{:x}", Sha256::digest(data.canonical_documents.as_bytes()));
        assert!(validate(&data).is_err());
    }
}
