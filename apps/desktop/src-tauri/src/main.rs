#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod bridge;
mod workspace;
use bridge::{Bridge, BridgeError, CoreRequest};
use tauri::{
    image::Image,
    menu::{Menu, MenuItem},
    tray::TrayIconBuilder,
    Manager, State,
};

#[tauri::command]
async fn core_request(
    request: CoreRequest,
    state: State<'_, Bridge>,
) -> Result<serde_json::Value, BridgeError> {
    state.dispatch(request).await
}

#[tauri::command]
fn connection_status(state: State<'_, Bridge>) -> serde_json::Value {
    state.status()
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, _, _| {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.unminimize();
                let _ = window.show();
                let _ = window.set_focus();
            }
        }))
        .manage(Bridge::load())
        .manage(workspace::Panels::default())
        .setup(|app| {
            let open = MenuItem::with_id(app, "open", "Open Jarvis", true, None::<&str>)?;
            let quit = MenuItem::with_id(
                app,
                "quit",
                "Exit Jarvis (stops owned local core)",
                true,
                None::<&str>,
            )?;
            let menu = Menu::with_items(app, &[&open, &quit])?;
            let mut rgba = vec![0u8; 32 * 32 * 4];
            for y in 0..32 {
                for x in 0..32 {
                    let i = (y * 32 + x) * 4;
                    let mark = ((19..=23).contains(&x) && (7..=23).contains(&y))
                        || ((22..=26).contains(&y) && (10..=22).contains(&x))
                        || ((8..=12).contains(&x) && (18..=24).contains(&y));
                    rgba[i..i + 4].copy_from_slice(if mark {
                        &[174, 196, 255, 255]
                    } else {
                        &[17, 26, 43, 255]
                    });
                }
            }
            TrayIconBuilder::new()
                .icon(Image::new_owned(rgba, 32, 32))
                .tooltip("Jarvis · Skyra Tech")
                .menu(&menu)
                .on_menu_event(|app, event| match event.id.as_ref() {
                    "open" => {
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.unminimize();
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                    "quit" => app.exit(0),
                    _ => {}
                })
                .build(app)?;
            Ok(())
        })
        .on_window_event(|window, event| {
            if window.label() == "main" {
                if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                    api.prevent_close();
                    let _ = window.hide();
                }
            }
        })
        .invoke_handler(tauri::generate_handler![
            core_request,
            connection_status,
            workspace::open_panel,
            workspace::workspace_action
        ])
        .run(tauri::generate_context!())
        .expect("Unable to start Jarvis Windows application");
}
