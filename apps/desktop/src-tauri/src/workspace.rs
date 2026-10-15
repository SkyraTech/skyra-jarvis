//! Native workspace windows. Renderer input can select only built-in panels, never URLs.
use serde::{Deserialize, Serialize};
use std::{
    collections::BTreeMap,
    fs,
    path::PathBuf,
    sync::{
        atomic::{AtomicU64, Ordering},
        Mutex,
    },
};
use tauri::{
    AppHandle, Manager, PhysicalPosition, PhysicalSize, State, WebviewUrl, WebviewWindow,
    WebviewWindowBuilder,
};

const VIEWS: [&str; 11] = [
    "Overview",
    "Jarvis core",
    "System map",
    "Repair proposals",
    "Coding runs",
    "Assignments",
    "Build jobs",
    "Approvals",
    "Conversations",
    "Activity",
    "Setup",
];
static NEXT: AtomicU64 = AtomicU64::new(0);
#[derive(Default)]
pub struct Panels(pub Mutex<BTreeMap<String, (String, Option<String>)>>);
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Bounds {
    x: i32,
    y: i32,
    width: u32,
    height: u32,
}
#[derive(Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct SavedWindow {
    label: String,
    view: String,
    project: Option<String>,
    bounds: Bounds,
    maximized: bool,
}
#[derive(Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Arrangement {
    version: u32,
    windows: Vec<SavedWindow>,
}

fn valid_panel(view: &str, project: &Option<String>) -> bool {
    VIEWS.contains(&view)
        && project.as_ref().is_none_or(|p| {
            p.len() == 32
                && p.bytes()
                    .all(|c| c.is_ascii_hexdigit() && !c.is_ascii_uppercase())
        })
}
fn valid_label(label: &str) -> bool {
    label == "main"
        || (label.starts_with("panel-")
            && label.len() <= 64
            && label
                .bytes()
                .all(|c| c.is_ascii_alphanumeric() || c == b'-'))
}
fn fail(_: impl std::fmt::Debug) -> String {
    "Window operation unavailable".into()
}
fn state_path(app: &AppHandle) -> Result<PathBuf, String> {
    if let Some(config) = std::env::var_os("JARVIS_DESKTOP_CONFIG") {
        let config = PathBuf::from(config);
        if config.is_absolute() {
            return config
                .parent()
                .map(|p| p.join("window-arrangement.json"))
                .ok_or_else(|| fail(()));
        }
    }
    Ok(app
        .path()
        .app_local_data_dir()
        .map_err(fail)?
        .join("window-arrangement.json"))
}
fn validate_arrangement(data: &Arrangement) -> bool {
    let labels: std::collections::BTreeSet<_> =
        data.windows.iter().map(|w| w.label.as_str()).collect();
    data.version == 1
        && !data.windows.is_empty()
        && data.windows.len() <= 9
        && labels.len() == data.windows.len()
        && data.windows.iter().all(|w| {
            valid_label(&w.label)
                && valid_panel(&w.view, &w.project)
                && (200..=32768).contains(&w.bounds.width)
                && (200..=32768).contains(&w.bounds.height)
        })
}
/// Keep saved windows reachable even if their previous monitor has gone away.
fn fit(bounds: &Bounds, areas: &[Bounds]) -> Bounds {
    let cx = i64::from(bounds.x) + i64::from(bounds.width) / 2;
    let cy = i64::from(bounds.y) + i64::from(bounds.height) / 2;
    let area = areas
        .iter()
        .find(|a| {
            cx >= i64::from(a.x)
                && cx < i64::from(a.x) + i64::from(a.width)
                && cy >= i64::from(a.y)
                && cy < i64::from(a.y) + i64::from(a.height)
        })
        .unwrap_or(&areas[0]);
    let width = bounds.width.min(area.width.saturating_sub(16).max(1));
    let height = bounds.height.min(area.height.saturating_sub(48).max(1));
    Bounds {
        x: bounds
            .x
            .clamp(area.x, area.x.saturating_add((area.width - width) as i32)),
        y: bounds.y.clamp(
            area.y,
            area.y
                .saturating_add((area.height - height - 32.min(area.height - height)) as i32),
        ),
        width,
        height,
    }
}
fn areas(window: &WebviewWindow) -> Result<Vec<Bounds>, String> {
    let monitors = window.available_monitors().map_err(fail)?;
    let result: Vec<_> = monitors
        .into_iter()
        .map(|m| {
            let a = m.work_area();
            Bounds {
                x: a.position.x,
                y: a.position.y,
                width: a.size.width,
                height: a.size.height,
            }
        })
        .filter(|a| a.width > 0 && a.height > 0)
        .collect();
    if result.is_empty() {
        return Err(fail(()));
    }
    Ok(result)
}
fn build(
    app: &AppHandle,
    label: &str,
    view: &str,
    project: &Option<String>,
) -> Result<WebviewWindow, String> {
    if !valid_label(label) || label == "main" || !valid_panel(view, project) {
        return Err(fail(()));
    }
    let slug = view.to_lowercase().replace(' ', "-");
    let url = format!(
        "index.html?panel={slug}&workspace={label}{}",
        project
            .as_ref()
            .map(|p| format!("&project={p}"))
            .unwrap_or_default()
    );
    WebviewWindowBuilder::new(app, label, WebviewUrl::App(url.into()))
        .title(format!("Jarvis · {view}"))
        .inner_size(1100.0, 780.0)
        .min_inner_size(640.0, 480.0)
        .resizable(true)
        .minimizable(true)
        .maximizable(true)
        .center()
        .build()
        .map_err(fail)
}
#[tauri::command]
pub async fn open_panel(
    app: AppHandle,
    state: State<'_, Panels>,
    view: String,
    project: Option<String>,
) -> Result<String, String> {
    if !valid_panel(&view, &project) {
        return Err(fail(()));
    }
    let mut registry = state.0.lock().map_err(fail)?;
    registry.retain(|label, _| app.get_webview_window(label).is_some());
    if registry.len() >= 8 {
        return Err(fail(()));
    }
    let stamp = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map_err(fail)?
        .as_millis();
    let label = format!("panel-{stamp}-{}", NEXT.fetch_add(1, Ordering::Relaxed));
    let window = build(&app, &label, &view, &project)?;
    // Fit initial geometry as well as restored geometry to the actual monitor work area.
    let position = window.outer_position().map_err(fail)?;
    let size = window.inner_size().map_err(fail)?;
    let bounds = fit(
        &Bounds {
            x: position.x,
            y: position.y,
            width: size.width,
            height: size.height,
        },
        &areas(&window)?,
    );
    window
        .set_size(PhysicalSize::new(bounds.width, bounds.height))
        .map_err(fail)?;
    window
        .set_position(PhysicalPosition::new(bounds.x, bounds.y))
        .map_err(fail)?;
    registry.insert(label.clone(), (view, project));
    Ok(label)
}
#[tauri::command]
pub async fn workspace_action(
    app: AppHandle,
    window: WebviewWindow,
    state: State<'_, Panels>,
    action: String,
    width: Option<u32>,
    height: Option<u32>,
) -> Result<(), String> {
    match action.as_str() {
        "show_all" => {
            for w in app.webview_windows().into_values() {
                w.unminimize().map_err(fail)?;
                w.show().map_err(fail)?;
            }
            Ok(())
        }
        "minimize" => window.minimize().map_err(fail),
        "maximize" => {
            if window.is_maximized().map_err(fail)? {
                window.unmaximize().map_err(fail)
            } else {
                window.maximize().map_err(fail)
            }
        }
        "fullscreen" => window
            .set_fullscreen(!window.is_fullscreen().map_err(fail)?)
            .map_err(fail),
        "resize" => {
            let (width, height) = (
                width.ok_or_else(|| fail(()))?,
                height.ok_or_else(|| fail(()))?,
            );
            if !(640..=7680).contains(&width) || !(480..=4320).contains(&height) {
                return Err(fail(()));
            }
            window.set_fullscreen(false).map_err(fail)?;
            window.unmaximize().map_err(fail)?;
            window
                .set_size(tauri::LogicalSize::new(width, height))
                .map_err(fail)
        }
        "save" => {
            let registry = state.0.lock().map_err(fail)?;
            let mut windows = Vec::new();
            for (label, w) in app.webview_windows() {
                if !valid_label(&label) {
                    continue;
                }
                let (view, project) = if label == "main" {
                    ("Overview".into(), None)
                } else {
                    registry.get(&label).cloned().ok_or_else(|| fail(()))?
                };
                // Save normal bounds only. Maximized windows are restored maximized after fitting.
                if w.is_minimized().map_err(fail)? || w.is_fullscreen().map_err(fail)? {
                    return Err(
                        "Restore minimized/fullscreen windows before saving arrangement".into(),
                    );
                }
                let pos = w.outer_position().map_err(fail)?;
                let size = w.inner_size().map_err(fail)?;
                windows.push(SavedWindow {
                    label,
                    view,
                    project,
                    bounds: Bounds {
                        x: pos.x,
                        y: pos.y,
                        width: size.width,
                        height: size.height,
                    },
                    maximized: w.is_maximized().map_err(fail)?,
                });
            }
            let data = Arrangement {
                version: 1,
                windows,
            };
            if !validate_arrangement(&data) {
                return Err(fail(()));
            }
            let path = state_path(&app)?;
            fs::create_dir_all(path.parent().ok_or_else(|| fail(()))?).map_err(fail)?;
            let temp = path.with_extension("tmp");
            fs::write(&temp, serde_json::to_vec(&data).map_err(fail)?).map_err(fail)?;
            fs::rename(temp, path).map_err(fail)
        }
        "restore" => {
            let path = state_path(&app)?;
            if fs::metadata(&path).map_err(fail)?.len() > 32768 {
                return Err(fail(()));
            }
            let data: Arrangement =
                serde_json::from_slice(&fs::read(path).map_err(fail)?).map_err(fail)?;
            if !validate_arrangement(&data) {
                return Err(fail(()));
            }
            let workareas = areas(&window)?;
            let mut registry = state.0.lock().map_err(fail)?;
            registry.retain(|label, _| app.get_webview_window(label).is_some());
            let missing = data
                .windows
                .iter()
                .filter(|w| w.label != "main" && app.get_webview_window(&w.label).is_none())
                .count();
            if registry.len() + missing > 8 {
                return Err(fail(()));
            }
            for saved in data.windows {
                let w = if let Some(w) = app.get_webview_window(&saved.label) {
                    w
                } else {
                    let w = build(&app, &saved.label, &saved.view, &saved.project)?;
                    registry.insert(saved.label.clone(), (saved.view, saved.project));
                    w
                };
                let b = fit(&saved.bounds, &workareas);
                w.set_fullscreen(false).map_err(fail)?;
                w.unmaximize().map_err(fail)?;
                w.set_size(PhysicalSize::new(b.width, b.height))
                    .map_err(fail)?;
                w.set_position(PhysicalPosition::new(b.x, b.y))
                    .map_err(fail)?;
                if saved.maximized {
                    w.maximize().map_err(fail)?;
                }
                w.show().map_err(fail)?;
                w.unminimize().map_err(fail)?;
            }
            Ok(())
        }
        _ => Err(fail(())),
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn fixed_panels_reject_urls_and_injected_projects() {
        assert!(valid_panel("Conversations", &Some("a".repeat(32))));
        assert!(!valid_panel("https://evil.test", &None));
        assert!(!valid_panel("Overview", &Some("../secret".into())));
        assert!(!valid_label("panel-../../secret"));
    }
    #[test]
    fn missing_monitor_recovers_to_visible_work_area() {
        let fitted = fit(
            &Bounds {
                x: -5000,
                y: 4000,
                width: 5000,
                height: 3000,
            },
            &[Bounds {
                x: 0,
                y: 0,
                width: 1920,
                height: 1040,
            }],
        );
        assert_eq!(0, fitted.x);
        assert!(fitted.width <= 1920 && fitted.height <= 1040);
        assert!(fitted.y >= 0 && fitted.y + fitted.height as i32 <= 1040);
    }
    #[test]
    fn negative_monitor_coordinates_are_preserved() {
        let fitted = fit(
            &Bounds {
                x: -1800,
                y: 100,
                width: 1000,
                height: 700,
            },
            &[
                Bounds {
                    x: 0,
                    y: 0,
                    width: 1920,
                    height: 1080,
                },
                Bounds {
                    x: -1920,
                    y: 0,
                    width: 1920,
                    height: 1080,
                },
            ],
        );
        assert_eq!(-1800, fitted.x);
        assert_eq!(100, fitted.y);
    }
    #[test]
    fn saved_manifest_rejects_duplicate_windows_and_bad_version() {
        let window = || SavedWindow {
            label: "main".into(),
            view: "Overview".into(),
            project: None,
            bounds: Bounds {
                x: 0,
                y: 0,
                width: 900,
                height: 700,
            },
            maximized: false,
        };
        assert!(!validate_arrangement(&Arrangement {
            version: 1,
            windows: vec![window(), window()]
        }));
        assert!(!validate_arrangement(&Arrangement {
            version: 2,
            windows: vec![window()]
        }));
    }
}
