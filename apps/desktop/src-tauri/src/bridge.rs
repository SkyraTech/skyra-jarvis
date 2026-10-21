//! Fixed loopback transport. Credentials never enter the renderer or a request argument.
use base64::Engine;
use reqwest::{Client, Method};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::{path::PathBuf, time::Duration};

#[derive(Debug, Serialize)]
pub struct BridgeError {
    code: &'static str,
    request_id: Option<String>,
}
fn error(code: &'static str) -> BridgeError {
    BridgeError {
        code,
        request_id: None,
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Config {
    port: u16,
    controller_token_dpapi: String,
    worker_token_dpapi: Option<String>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CoreRequest {
    action: String,
    project: Option<String>,
    id: Option<String>,
    checksum: Option<String>,
    after: Option<u64>,
    body: Option<Value>,
}

struct Credentials {
    port: u16,
    controller: String,
    worker: Option<String>,
}
pub struct Bridge {
    credentials: Option<Credentials>,
    client: Client,
}

impl CoreRequest {
    pub fn specification_export(id: String, checksum: String) -> Self {
        Self {
            action: "prepare_specification_export".into(),
            project: None,
            id: Some(id),
            checksum: None,
            after: None,
            body: Some(json!({"expected_sha256": checksum})),
        }
    }
}

fn token_valid(token: &str) -> bool {
    (32..=256).contains(&token.len())
        && token
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b == b'_' || b == b'-')
}

#[cfg(windows)]
fn decrypt(encoded: &str) -> Result<String, BridgeError> {
    #[repr(C)]
    struct Blob {
        len: u32,
        data: *mut u8,
    }
    #[link(name = "crypt32")]
    extern "system" {
        fn CryptUnprotectData(
            input: *const Blob,
            description: *mut *mut u16,
            entropy: *const Blob,
            reserved: *mut std::ffi::c_void,
            prompt: *const std::ffi::c_void,
            flags: u32,
            output: *mut Blob,
        ) -> i32;
    }
    #[link(name = "kernel32")]
    extern "system" {
        fn LocalFree(memory: *mut std::ffi::c_void) -> *mut std::ffi::c_void;
    }
    let mut bytes = base64::engine::general_purpose::STANDARD
        .decode(encoded)
        .map_err(|_| error("not_configured"))?;
    if bytes.is_empty() || bytes.len() > 8192 {
        return Err(error("not_configured"));
    }
    let input = Blob {
        len: bytes.len() as u32,
        data: bytes.as_mut_ptr(),
    };
    let mut output = Blob {
        len: 0,
        data: std::ptr::null_mut(),
    };
    // DPAPI allocation is copied and freed exactly once. No description/entropy is requested.
    if unsafe {
        CryptUnprotectData(
            &input,
            std::ptr::null_mut(),
            std::ptr::null(),
            std::ptr::null_mut(),
            std::ptr::null(),
            1,
            &mut output,
        )
    } == 0
    {
        return Err(error("not_configured"));
    }
    let result = if output.data.is_null() || output.len > 256 {
        Err(error("not_configured"))
    } else {
        String::from_utf8(
            unsafe { std::slice::from_raw_parts(output.data, output.len as usize) }.to_vec(),
        )
        .map_err(|_| error("not_configured"))
    };
    if !output.data.is_null() {
        unsafe {
            LocalFree(output.data.cast());
        }
    }
    let token = result?;
    if !token_valid(&token) {
        return Err(error("not_configured"));
    }
    Ok(token)
}

#[cfg(not(windows))]
fn decrypt(_: &str) -> Result<String, BridgeError> {
    Err(error("not_configured"))
}

fn identifier(value: &Option<String>) -> Result<&str, BridgeError> {
    let id = value.as_deref().ok_or_else(|| error("invalid_input"))?;
    if id.len() != 32
        || !id
            .bytes()
            .all(|b| b.is_ascii_hexdigit() && !b.is_ascii_uppercase())
    {
        return Err(error("invalid_input"));
    }
    Ok(id)
}

fn route(request: &CoreRequest) -> Result<(Method, String, bool), BridgeError> {
    let get = Method::GET;
    let post = Method::POST;
    let route = match request.action.as_str() {
        "setup" => (get, "/v1/setup".into(), false),
        "projects" => (get, "/v1/projects".into(), false),
        "create_project" => (post, "/v1/projects".into(), false),
        "policy" => (
            Method::PUT,
            format!("/v1/projects/{}/policy", identifier(&request.project)?),
            false,
        ),
        "operations" => (
            get,
            format!(
                "/v1/projects/{}/operations?before={}",
                identifier(&request.project)?,
                request.after.unwrap_or(0)
            ),
            false,
        ),
        "acknowledge_operation" => (
            post,
            format!("/v1/operations/{}/acknowledge", identifier(&request.id)?),
            false,
        ),
        "dashboard" => (
            get,
            format!("/v1/projects/{}/dashboard", identifier(&request.project)?),
            false,
        ),
        "preview_scaffold"
        | "create_scaffold"
        | "scaffold_status"
        | "preview_scaffold_registration"
        | "register_scaffold"
        | "scaffold_registration" => (
            post,
            format!(
                "/v1/specifications/{}/scaffolds/{}",
                identifier(&request.id)?,
                match request.action.as_str() {
                    "preview_scaffold" => "preview",
                    "create_scaffold" => "create",
                    "preview_scaffold_registration" => "registration-preview",
                    "register_scaffold" => "register",
                    "scaffold_registration" => "registration",
                    _ => "status",
                }
            ),
            false,
        ),
        "preview_existing_project"
        | "admit_existing_project"
        | "existing_project_status"
        | "preview_existing_registration"
        | "register_existing_project" => (
            post,
            format!(
                "/v1/specifications/{}/existing-projects/{}",
                identifier(&request.id)?,
                match request.action.as_str() {
                    "preview_existing_project" => "preview",
                    "admit_existing_project" => "admit",
                    "existing_project_status" => "status",
                    "preview_existing_registration" => "registration-preview",
                    _ => "register",
                }
            ),
            false,
        ),
        "revise_specification" | "prepare_specification_export" => (
            post,
            format!(
                "/v1/specifications/{}/{}",
                identifier(&request.id)?,
                if request.action == "revise_specification" {
                    "revisions"
                } else {
                    "export"
                }
            ),
            false,
        ),
        "specifications" | "publish_specification" => (
            if request.action == "specifications" {
                get
            } else {
                post
            },
            format!(
                "/v1/projects/{}/specifications",
                identifier(&request.project)?
            ),
            false,
        ),
        "specification" | "approve_specification" => (
            if request.action == "specification" {
                get
            } else {
                post
            },
            format!(
                "/v1/specifications/{}{}",
                identifier(&request.id)?,
                if request.action == "approve_specification" {
                    "/approve"
                } else {
                    ""
                }
            ),
            false,
        ),
        "conversation" => (
            post,
            format!(
                "/v1/projects/{}/conversations",
                identifier(&request.project)?
            ),
            false,
        ),
        "coding_history" => (
            get,
            format!(
                "/v1/conversations/{}/coding-history?before={}",
                identifier(&request.id)?,
                request.after.unwrap_or(0)
            ),
            false,
        ),
        "messages" => (
            get,
            format!(
                "/v1/conversations/{}/messages?after={}&limit=10",
                identifier(&request.id)?,
                request.after.unwrap_or(0)
            ),
            false,
        ),
        "message" => (
            post,
            format!("/v1/conversations/{}/messages", identifier(&request.id)?),
            false,
        ),
        "create_turn" | "turns" => (
            if request.action == "turns" { get } else { post },
            format!("/v1/conversations/{}/model-turns", identifier(&request.id)?),
            false,
        ),
        "turn" => (
            get,
            format!("/v1/model-turns/{}", identifier(&request.id)?),
            false,
        ),
        "generate_turn" | "interrupt_turn" => (
            post,
            format!(
                "/v1/model-turns/{}/{}",
                identifier(&request.id)?,
                if request.action == "generate_turn" {
                    "generate"
                } else {
                    "interrupt"
                }
            ),
            false,
        ),
        "create_proposal" => (
            post,
            format!(
                "/v1/projects/{}/repair-proposals",
                identifier(&request.project)?
            ),
            false,
        ),
        "proposal" => (
            get,
            format!("/v1/repair-proposals/{}", identifier(&request.id)?),
            false,
        ),
        "generate" | "accept" | "interrupt" => (
            post,
            format!(
                "/v1/repair-proposals/{}/{}",
                identifier(&request.id)?,
                request.action
            ),
            false,
        ),
        "continuation_preview" | "continue_project" | "continuation_status" => (
            post,
            format!(
                "/v1/deliveries/{}/{}",
                identifier(&request.id)?,
                match request.action.as_str() {
                    "continuation_preview" => "continuation-preview",
                    "continue_project" => "continue",
                    _ => "continuation-status",
                }
            ),
            false,
        ),
        "delivery_preview" | "prepare_delivery" | "deliveries" => (
            if request.action == "deliveries" {
                get
            } else {
                post
            },
            format!(
                "/v1/coding-runs/{}/{}",
                identifier(&request.id)?,
                if request.action == "delivery_preview" {
                    "delivery-preview"
                } else {
                    "deliveries"
                }
            ),
            false,
        ),
        "build_jobs" | "create_build_job" => (
            if request.action == "build_jobs" {
                get
            } else {
                post
            },
            format!("/v1/projects/{}/build-jobs", identifier(&request.project)?),
            false,
        ),
        "build_job" | "control_build_job" | "accept_build_proposal" | "retry_build_generation" => (
            if request.action == "build_job" {
                get
            } else {
                post
            },
            format!(
                "/v1/build-jobs/{}{}",
                identifier(&request.id)?,
                match request.action.as_str() {
                    "control_build_job" => "/control",
                    "accept_build_proposal" => "/accept-proposal",
                    "retry_build_generation" => "/retry-generation",
                    _ => "",
                }
            ),
            false,
        ),
        "assignments" | "create_assignment" => (
            if request.action == "assignments" {
                get
            } else {
                post
            },
            format!("/v1/projects/{}/assignments", identifier(&request.project)?),
            false,
        ),
        "control_assignment" => (
            post,
            format!("/v1/assignments/{}/control", identifier(&request.id)?),
            false,
        ),
        "advance_delivery" => (
            post,
            format!("/v1/deliveries/{}/advance", identifier(&request.id)?),
            true,
        ),
        "run" => (
            get,
            format!("/v1/coding-runs/{}", identifier(&request.id)?),
            false,
        ),
        "advance" => (
            post,
            format!("/v1/coding-runs/{}/advance", identifier(&request.id)?),
            true,
        ),
        "cancel_run" => (
            post,
            format!("/v1/coding-runs/{}/cancel", identifier(&request.id)?),
            false,
        ),
        "approval" => (
            get,
            format!("/v1/approvals/{}", identifier(&request.id)?),
            false,
        ),
        "decide" => (
            post,
            format!("/v1/approvals/{}/decision", identifier(&request.id)?),
            false,
        ),
        "evidence" => {
            let checksum = request
                .checksum
                .as_deref()
                .ok_or_else(|| error("invalid_input"))?;
            if checksum.len() != 64
                || !checksum
                    .bytes()
                    .all(|b| b.is_ascii_hexdigit() && !b.is_ascii_uppercase())
            {
                return Err(error("invalid_input"));
            }
            (
                get,
                format!(
                    "/v1/tasks/{}/evidence/{}",
                    identifier(&request.id)?,
                    checksum
                ),
                false,
            )
        }
        _ => return Err(error("invalid_input")),
    };
    Ok(route)
}

impl Bridge {
    pub fn load() -> Self {
        let config_path = std::env::var_os("JARVIS_DESKTOP_CONFIG")
            .map(PathBuf::from)
            .or_else(|| {
                std::env::var_os("LOCALAPPDATA")
                    .map(|p| PathBuf::from(p).join("Skyra/Jarvis/desktop.json"))
            });
        let credentials = (|| {
            let path = config_path?;
            if std::fs::metadata(&path).ok()?.len() > 65536 {
                return None;
            }
            let config: Config = serde_json::from_slice(&std::fs::read(path).ok()?).ok()?;
            if config.port < 1024 {
                return None;
            }
            let controller = decrypt(&config.controller_token_dpapi).ok()?;
            let worker = config
                .worker_token_dpapi
                .as_deref()
                .map(decrypt)
                .transpose()
                .ok()?;
            Some(Credentials {
                port: config.port,
                controller,
                worker,
            })
        })();
        Self {
            credentials,
            client: Client::builder()
                .no_proxy()
                .redirect(reqwest::redirect::Policy::none())
                .retry(reqwest::retry::never())
                .connect_timeout(Duration::from_secs(3))
                .timeout(Duration::from_secs(125))
                .build()
                .expect("Unable to initialize loopback transport"),
        }
    }

    pub fn status(&self) -> Value {
        json!({ "configured": self.credentials.is_some(), "worker_configured": self.credentials.as_ref().is_some_and(|c| c.worker.is_some()) })
    }

    pub async fn dispatch(&self, request: CoreRequest) -> Result<Value, BridgeError> {
        let (method, path, worker) = route(&request)?;
        let credentials = self
            .credentials
            .as_ref()
            .ok_or_else(|| error("not_configured"))?;
        let token = if worker {
            credentials
                .worker
                .as_deref()
                .ok_or_else(|| error("worker_unavailable"))?
        } else {
            &credentials.controller
        };
        let mut outgoing = self
            .client
            .request(
                method,
                format!("http://127.0.0.1:{}{}", credentials.port, path),
            )
            .bearer_auth(token);
        if let Some(body) = request.body {
            if serde_json::to_vec(&body)
                .map_err(|_| error("invalid_input"))?
                .len()
                > 131072
            {
                return Err(error("invalid_input"));
            }
            outgoing = outgoing.json(&body);
        }
        let mut response = outgoing.send().await.map_err(|e| {
            error(if e.is_timeout() {
                "timeout"
            } else {
                "disconnected"
            })
        })?;
        let status = response.status();
        let request_id = response
            .headers()
            .get("x-request-id")
            .and_then(|v| v.to_str().ok())
            .filter(|v| v.len() == 32 && v.bytes().all(|b| b.is_ascii_hexdigit()))
            .map(String::from);
        let mut bytes = Vec::new();
        while let Some(chunk) = response.chunk().await.map_err(|_| error("disconnected"))? {
            if bytes.len() + chunk.len() > 2_097_152 {
                return Err(error("response_too_large"));
            }
            bytes.extend_from_slice(&chunk);
        }
        if !status.is_success() {
            let code = match status.as_u16() {
                401 => "unauthenticated",
                403 => "forbidden",
                409 => "conflict",
                422 => "invalid_input",
                503 => "disconnected",
                _ => "core_error",
            };
            return Err(BridgeError { code, request_id });
        }
        serde_json::from_slice(&bytes).map_err(|_| error("invalid_response"))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn request(action: &str) -> CoreRequest {
        CoreRequest {
            action: action.into(),
            project: Some("a".repeat(32)),
            id: Some("b".repeat(32)),
            checksum: Some("c".repeat(64)),
            after: None,
            body: None,
        }
    }
    #[test]
    fn conversation_routes_are_fixed_and_controller_only() {
        let (method, path, worker) = route(&request("coding_history")).unwrap();
        assert_eq!(method, Method::GET);
        assert!(path.contains("/coding-history?before=0"));
        assert!(!worker);
        let mut invalid = request("coding_history");
        invalid.id = Some("../other".into());
        assert!(route(&invalid).is_err());
        for (action, suffix, method) in [
            ("create_turn", "/model-turns", Method::POST),
            ("turns", "/model-turns", Method::GET),
            ("turn", "", Method::GET),
            ("generate_turn", "/generate", Method::POST),
            ("interrupt_turn", "/interrupt", Method::POST),
        ] {
            let request: CoreRequest =
                serde_json::from_value(json!({"action": action, "id": "a".repeat(32)})).unwrap();
            let (verb, path, worker) = route(&request).unwrap();
            assert_eq!(verb, method);
            assert!(path.ends_with(suffix));
            assert!(!worker);
        }
        let request: CoreRequest =
            serde_json::from_value(json!({"action": "generate_turn", "id": "../policy"})).unwrap();
        assert!(route(&request).is_err());
    }

    #[test]
    fn specification_routes_use_controller_and_reject_traversal() {
        for action in [
            "specifications",
            "publish_specification",
            "specification",
            "approve_specification",
            "revise_specification",
            "prepare_specification_export",
            "preview_scaffold",
            "create_scaffold",
            "scaffold_status",
            "preview_scaffold_registration",
            "register_scaffold",
            "scaffold_registration",
            "preview_existing_project",
            "admit_existing_project",
            "existing_project_status",
            "preview_existing_registration",
            "register_existing_project",
        ] {
            let req = request(action);
            let (verb, path, worker) = route(&req).unwrap();
            assert!(!worker);
            assert_eq!(
                verb,
                if action == "specifications" || action == "specification" {
                    Method::GET
                } else {
                    Method::POST
                }
            );
            assert!(path.contains("/specifications"));
            let mut invalid = request(action);
            invalid.project = Some("../bad".into());
            invalid.id = Some("../bad".into());
            assert!(route(&invalid).is_err());
        }
    }

    #[test]
    fn arbitrary_urls_and_methods_are_not_routes() {
        for action in [
            "http://example.com",
            "shell",
            "set_policy",
            "complete",
            "start",
            "GET /v1/projects",
        ] {
            assert!(route(&request(action)).is_err());
        }
    }
    #[test]
    fn delivery_routes_separate_review_and_worker_execution() {
        for action in [
            "delivery_preview",
            "prepare_delivery",
            "deliveries",
            "advance_delivery",
            "continuation_preview",
            "continue_project",
            "continuation_status",
        ] {
            let (method, path, worker) = route(&request(action)).unwrap();
            assert_eq!(worker, action == "advance_delivery");
            assert_eq!(
                method,
                if action == "deliveries" {
                    Method::GET
                } else {
                    Method::POST
                }
            );
            assert!(path.contains("/deliver"));
            let mut invalid = request(action);
            invalid.id = Some("../source".into());
            assert!(route(&invalid).is_err());
        }
    }
    #[test]
    fn assignment_controls_are_controller_only_and_tick_is_not_a_renderer_route() {
        for action in ["assignments", "create_assignment", "control_assignment"] {
            let (_, path, worker) = route(&request(action)).unwrap();
            assert!(!worker);
            assert!(path.contains("assignments"));
            let mut invalid = request(action);
            invalid.id = Some("../outside".into());
            invalid.project = Some("../outside".into());
            assert!(route(&invalid).is_err());
        }
        assert!(route(&request("runner_tick")).is_err());
    }
    #[test]
    fn build_job_routes_are_fixed_controller_actions() {
        for action in [
            "build_jobs",
            "create_build_job",
            "build_job",
            "control_build_job",
            "accept_build_proposal",
            "retry_build_generation",
        ] {
            let (method, path, worker) = route(&request(action)).unwrap();
            assert!(!worker);
            assert!(path.contains("/build-jobs"));
            assert_eq!(
                method,
                if action == "build_jobs" || action == "build_job" {
                    Method::GET
                } else {
                    Method::POST
                }
            );
            let mut invalid = request(action);
            invalid.id = Some("../outside".into());
            invalid.project = Some("../outside".into());
            assert!(route(&invalid).is_err());
        }
    }
    #[test]
    fn operations_routes_cannot_execute_or_expand_scope() {
        let (method, path, worker) = route(&request("operations")).unwrap();
        assert_eq!(method, Method::GET);
        assert!(path.ends_with("/operations?before=0"));
        assert!(!worker);
        let (method, path, worker) = route(&request("acknowledge_operation")).unwrap();
        assert_eq!(method, Method::POST);
        assert!(path.ends_with("/acknowledge"));
        assert!(!worker);
        let mut invalid = request("operations");
        invalid.project = Some("../outside".into());
        assert!(route(&invalid).is_err());
        let mut invalid = request("acknowledge_operation");
        invalid.id = Some("../outside".into());
        assert!(route(&invalid).is_err());
    }
    #[test]
    fn traversal_and_query_injection_are_rejected() {
        let mut req = request("proposal");
        req.id = Some("../projects?token=secret".into());
        assert!(route(&req).is_err());
        let mut req = request("evidence");
        req.checksum = Some("../".into());
        assert!(route(&req).is_err());
    }
    #[test]
    fn worker_token_is_reserved_for_run_advance() {
        assert!(route(&request("advance")).unwrap().2);
        for action in ["decide", "generate", "accept", "cancel_run", "dashboard"] {
            assert!(!route(&request(action)).unwrap().2);
        }
    }
    #[test]
    fn unknown_fields_and_invalid_tokens_are_rejected() {
        assert!(
            serde_json::from_str::<CoreRequest>(r#"{"action":"projects","token":"secret"}"#)
                .is_err()
        );
        assert!(!token_valid("secret\r\nHost: attacker"));
        assert!(token_valid(&"a".repeat(32)));
    }
}
