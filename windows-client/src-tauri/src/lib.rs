use std::process::Command;
use tauri::Emitter;

#[tauri::command]
async fn get_adb_devices() -> Result<Vec<String>, String> {
    let output = Command::new("adb")
        .arg("devices")
        .output()
        .map_err(|e| e.to_string())?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    let devices: Vec<String> = stdout
        .lines()
        .skip(1) // Skip "List of devices attached"
        .filter_map(|line| {
            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.len() >= 2 && parts[1] == "device" {
                Some(parts[0].to_string())
            } else {
                None
            }
        })
        .collect();

    Ok(devices)
}

#[tauri::command]
async fn run_adb_forward(port: u16) -> Result<(), String> {
    Command::new("adb")
        .args(["forward", &format!("tcp:{}", port), &format!("tcp:{}", port)])
        .output()
        .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
async fn start_hybrid_engine(path: String) -> Result<String, String> {
    // Start the Python core engine as a sub-process
    let child = Command::new("python")
        .arg(path)
        .spawn()
        .map_err(|e| e.to_string())?;
        
    Ok(format!("Engine started with PID: {}", child.id()))
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            get_adb_devices,
            run_adb_forward,
            start_hybrid_engine
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
