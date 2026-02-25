package com.example.hybridlink.ui.screens

import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import com.example.hybridlink.ui.theme.*
import com.example.hybridlink.util.ConnectivityObserver
import com.example.hybridlink.util.NetworkConnectivityObserver
import com.example.hybridlink.util.UsbConnectionObserver
import kotlinx.coroutines.delay

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(navController: NavController) {
    val context = androidx.compose.ui.platform.LocalContext.current
    val networkObserver = remember { NetworkConnectivityObserver(context) }
    val usbObserver = remember { UsbConnectionObserver(context) }
    
    val networkStatus by networkObserver.observe().collectAsState(initial = ConnectivityObserver.Status.Unavailable)
    val usbStatus by usbObserver.observe().collectAsState(initial = UsbConnectionObserver.Status.Disconnected)

    // HybridFileXfer inspired states
    var isServerRunning by remember { mutableStateOf(false) }
    var serverStatusText by remember { mutableStateOf("Ready to Start") }
    var accessMode by remember { mutableStateOf("NORMAL") }
    
    // Checked Channels
    var useWifiMain by remember { mutableStateOf(true) }
    var useWifiWfa by remember { mutableStateOf(false) }
    var useUsbTether by remember { mutableStateOf(false) }
    var useUsbAdb by remember { mutableStateOf(true) }

    val scrollState = rememberScrollState()

    LaunchedEffect(isServerRunning) {
        if (isServerRunning) {
            serverStatusText = "Starting IO Services..."
            delay(800)
            serverStatusText = "Waiting for PC Connection..."
        } else {
            serverStatusText = "Server Stopped"
        }
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(
                Brush.verticalGradient(
                    colors = listOf(HybridDark, HybridSurface)
                )
            )
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(20.dp)
                .verticalScroll(scrollState)
        ) {
            // Header
            Row(
                modifier = Modifier.fillMaxWidth().padding(bottom = 16.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "HYBRIDLINK",
                        style = MaterialTheme.typography.headlineMedium,
                        fontWeight = FontWeight.ExtraBold,
                        color = TextPrimary,
                        letterSpacing = (-1).sp
                    )
                    Text(
                        text = "Multipath Engine Control",
                        style = MaterialTheme.typography.bodySmall,
                        color = HybridCyan
                    )
                }
                IconButton(
                    onClick = { navController.navigate("settings") },
                    colors = IconButtonDefaults.iconButtonColors(containerColor = HybridSecondary)
                ) {
                    Icon(Icons.Filled.Settings, contentDescription = "Settings", tint = TextPrimary)
                }
            }

            // --- SERVER CONTROL CARD ---
            Card(
                modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp),
                colors = CardDefaults.cardColors(containerColor = if (isServerRunning) HybridCyan.copy(alpha=0.15f) else HybridSecondary),
                shape = RoundedCornerShape(20.dp),
            ) {
                Column(modifier = Modifier.padding(20.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(modifier = Modifier
                            .size(12.dp)
                            .background(if (isServerRunning) HybridCyan else Color.Gray, RoundedCornerShape(50))
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = if (isServerRunning) "SERVER ACTIVE" else "SERVER INACTIVE",
                            color = if (isServerRunning) HybridCyan else TextDim,
                            fontWeight = FontWeight.Bold,
                            fontSize = 12.sp,
                            letterSpacing = 1.sp
                        )
                    }
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(serverStatusText, color = TextPrimary, fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
                    
                    Spacer(modifier = Modifier.height(16.dp))
                    Button(
                        onClick = { isServerRunning = !isServerRunning },
                        colors = ButtonDefaults.buttonColors(
                            containerColor = if (isServerRunning) HybridPurple else HybridCyan,
                            contentColor = if (isServerRunning) Color.White else HybridDark
                        ),
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Icon(if (isServerRunning) Icons.Filled.Stop else Icons.Filled.PlayArrow, contentDescription = null)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(if (isServerRunning) "Stop Engine" else "Start Server & Await PC", fontWeight = FontWeight.Bold)
                    }
                }
            }

            // --- ACCESS MODE SELECTION ---
            Text(
                "DIRECTORY ACCESS MODE",
                style = MaterialTheme.typography.labelMedium,
                color = TextSecondary,
                letterSpacing = 2.sp,
                modifier = Modifier.padding(top = 16.dp, bottom = 8.dp)
            )
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                ModeSelectionChip("NORMAL", accessMode == "NORMAL", Icons.Filled.Folder) { accessMode = "NORMAL" }
                ModeSelectionChip("SHIZUKU", accessMode == "SHIZUKU", Icons.Filled.Terminal) { accessMode = "SHIZUKU" }
                ModeSelectionChip("ROOT", accessMode == "ROOT", Icons.Filled.AdminPanelSettings) { accessMode = "ROOT" }
            }
            if (accessMode != "NORMAL") {
                Text("⚠️ Allows access to protected /Android/data directories via ADB IPC.", color = HybridPurple, fontSize = 11.sp, modifier = Modifier.padding(top=4.dp))
            }

            // --- NETWORK CHANNELS SELECTION ---
            Text(
                "TRANSPORT CHANNELS & INTERFACES",
                style = MaterialTheme.typography.labelMedium,
                color = TextSecondary,
                letterSpacing = 2.sp,
                modifier = Modifier.padding(top = 24.dp, bottom = 8.dp)
            )
            
            Card(
                colors = CardDefaults.cardColors(containerColor = HybridSecondary),
                shape = RoundedCornerShape(16.dp)
            ) {
                Column(modifier = Modifier.padding(vertical = 8.dp)) {
                    ChannelToggleRow(
                        title = "Primary WiFi (wlan0)",
                        ip = "192.168.1.114",
                        checked = useWifiMain,
                        onCheckedChange = { useWifiMain = it }
                    )
                    Divider(color = Color.White.copy(alpha = 0.05f))
                    ChannelToggleRow(
                        title = "Auxiliary WiFi / WFA (wlan1)",
                        ip = "192.168.1.182",
                        checked = useWifiWfa,
                        onCheckedChange = { useWifiWfa = it }
                    )
                    Divider(color = Color.White.copy(alpha = 0.05f))
                    ChannelToggleRow(
                        title = "USB Network Tethering (usb0)",
                        ip = "192.168.42.129",
                        checked = useUsbTether,
                        onCheckedChange = { useUsbTether = it }
                    )
                    Divider(color = Color.White.copy(alpha = 0.05f))
                    ChannelToggleRow(
                        title = "USB ADB Forwarding (Loopback)",
                        ip = "127.0.0.1:9000",
                        checked = useUsbAdb,
                        onCheckedChange = { useUsbAdb = it }
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(32.dp))

            // --- FILE ACTIONS ---
            Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                ActionCard(
                    title = "File Transfer Manager",
                    subtitle = "Dual-pane directory navigator",
                    icon = Icons.Filled.CompareArrows,
                    color = HybridCyan,
                    onClick = { navController.navigate("transfer/send") },
                    enabled = isServerRunning
                )
                ActionCard(
                    title = "Bookmarks",
                    subtitle = "Quick access to saved folders",
                    icon = Icons.Filled.Bookmarks,
                    color = HybridPurple,
                    onClick = { /* Open Bookmarks */ }
                )
            }
            Spacer(modifier = Modifier.height(32.dp))
        }
    }
}

@Composable
fun RowScope.ModeSelectionChip(text: String, isSelected: Boolean, icon: ImageVector, onClick: () -> Unit) {
    Surface(
        modifier = Modifier.weight(1f).height(48.dp),
        color = if (isSelected) HybridCyan.copy(alpha = 0.2f) else HybridSecondary,
        shape = RoundedCornerShape(12.dp),
        border = if (isSelected) androidx.compose.foundation.BorderStroke(1.dp, HybridCyan) else null,
        onClick = onClick
    ) {
        Row(horizontalArrangement = Arrangement.Center, verticalAlignment = Alignment.CenterVertically) {
            Icon(icon, contentDescription = null, tint = if (isSelected) HybridCyan else TextDim, modifier = Modifier.size(16.dp))
            Spacer(modifier = Modifier.width(6.dp))
            Text(text, color = if (isSelected) HybridCyan else TextSecondary, fontSize = 12.sp, fontWeight = FontWeight.Bold)
        }
    }
}

@Composable
fun ChannelToggleRow(title: String, ip: String, checked: Boolean, onCheckedChange: (Boolean) -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(title, color = TextPrimary, fontWeight = FontWeight.Medium, fontSize = 14.sp)
            Text(ip, color = HybridCyan, fontSize = 12.sp, fontFamily = androidx.compose.ui.text.font.FontFamily.Monospace)
        }
        Switch(
            checked = checked,
            onCheckedChange = onCheckedChange,
            colors = SwitchDefaults.colors(
                checkedThumbColor = HybridDark,
                checkedTrackColor = HybridCyan,
                uncheckedThumbColor = TextSecondary,
                uncheckedTrackColor = HybridSecondary
            )
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ActionCard(
    title: String,
    subtitle: String,
    icon: ImageVector,
    color: Color,
    onClick: () -> Unit,
    enabled: Boolean = true
) {
    Surface(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth().alpha(if (enabled) 1f else 0.5f),
        color = HybridSurface,
        shape = RoundedCornerShape(24.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, color.copy(alpha = 0.2f)),
        enabled = enabled
    ) {
        Row(
            modifier = Modifier.padding(20.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(48.dp)
                    .background(color.copy(alpha = 0.1f), RoundedCornerShape(12.dp)),
                contentAlignment = Alignment.Center
            ) {
                Icon(icon, contentDescription = null, tint = color)
            }
            Spacer(modifier = Modifier.width(16.dp))
            Column {
                Text(
                    text = title,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = TextPrimary
                )
                Text(
                    text = subtitle,
                    style = MaterialTheme.typography.bodySmall,
                    color = TextSecondary
                )
            }
            Spacer(modifier = Modifier.weight(1f))
            Icon(Icons.Filled.ChevronRight, contentDescription = null, tint = TextDim)
        }
    }
}

val TextDim = Color(0xFF475569)