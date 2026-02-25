package com.example.hybridlink.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import androidx.compose.runtime.*
import com.example.hybridlink.ui.theme.*
import com.example.hybridlink.util.ConnectivityObserver
import com.example.hybridlink.util.NetworkConnectivityObserver
import com.example.hybridlink.util.UsbConnectionObserver

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(navController: NavController) {
    val context = androidx.compose.ui.platform.LocalContext.current
    val networkObserver = remember { NetworkConnectivityObserver(context) }
    val usbObserver = remember { UsbConnectionObserver(context) }
    
    val networkStatus by networkObserver.observe().collectAsState(initial = ConnectivityObserver.Status.Unavailable)
    val usbStatus by usbObserver.observe().collectAsState(initial = UsbConnectionObserver.Status.Disconnected)

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
                .padding(24.dp)
        ) {
            // Header
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "HYBRIDLINK.IO",
                        style = MaterialTheme.typography.headlineMedium,
                        fontWeight = FontWeight.ExtraBold,
                        color = TextPrimary,
                        letterSpacing = (-1).sp
                    )
                    Text(
                        text = "Multipath File Transfer",
                        style = MaterialTheme.typography.bodySmall,
                        color = TextSecondary
                    )
                }
                IconButton(
                    onClick = { navController.navigate("settings") },
                    colors = IconButtonDefaults.iconButtonColors(
                        containerColor = HybridSecondary
                    )
                ) {
                    Icon(Icons.Filled.Settings, contentDescription = "Settings", color = TextPrimary)
                }
            }

            Spacer(modifier = Modifier.weight(1f))

            // Logo Icon Area
            Box(
                modifier = Modifier
                    .size(120.dp)
                    .align(Alignment.CenterHorizontally)
                    .background(
                        Brush.linearGradient(listOf(HybridCyan, HybridPurple)),
                        RoundedCornerShape(32.dp)
                    ),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Filled.CloudUpload,
                    contentDescription = null,
                    modifier = Modifier.size(60.dp),
                    tint = HybridDark
                )
            }

            Spacer(modifier = Modifier.weight(1f))

            // Action Buttons
            Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                ActionCard(
                    title = "Send File",
                    subtitle = "High-speed multipath upload",
                    icon = Icons.Filled.ArrowUpward,
                    color = HybridCyan,
                    onClick = { navController.navigate("transfer/send") }
                )
                ActionCard(
                    title = "Receive File",
                    subtitle = "Secure local discovery",
                    icon = Icons.Filled.ArrowDownward,
                    color = HybridPurple,
                    onClick = { navController.navigate("transfer/receive") }
                )
            }

            Spacer(modifier = Modifier.height(32.dp))

            // Stats Footer
            Surface(
                modifier = Modifier.fillMaxWidth(),
                color = HybridSecondary,
                shape = RoundedCornerShape(20.dp),
                border = AssistChipDefaults.assistChipBorder(borderColor = Color.White.copy(0.05f))
            ) {
                Row(
                    modifier = Modifier.padding(16.dp),
                    horizontalArrangement = Arrangement.SpaceAround
                ) {
                    StatusItem(
                        label = "USB", 
                        status = if (usbStatus == UsbConnectionObserver.Status.Connected) "CONNECTED" else "STOPPED",
                        color = if (usbStatus == UsbConnectionObserver.Status.Connected) HybridCyan else TextDim
                    )
                    StatusItem(
                        label = "WIFI", 
                        status = if (networkStatus == ConnectivityObserver.Status.Available) "ACTIVE" else "PENDING",
                        color = if (networkStatus == ConnectivityObserver.Status.Available) HybridPurple else TextDim
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(32.dp))
            
            // Nearby Devices Radar
            NearbyDevicesRadar()
        }
    }
}

@Composable
fun NearbyDevicesRadar() {
    Column {
        Text(
            "NEARBY DEVICES",
            style = MaterialTheme.typography.labelMedium,
            color = TextSecondary,
            letterSpacing = 2.sp
        )
        Spacer(modifier = Modifier.height(16.dp))
        
        // Mock Discovered Devices
        DeviceDiscoveryCard(name = "Windows Station", transports = listOf("WiFi", "BT", "USB"), os = "Windows 11", mode = "APP")
        Spacer(modifier = Modifier.height(12.dp))
        DeviceDiscoveryCard(name = "Kitchen Chromebook", transports = listOf("WiFi"), os = "ChromeOS", mode = "BROWSER")
        Spacer(modifier = Modifier.height(12.dp))
        DeviceDiscoveryCard(name = "Office Mac", transports = listOf("WiFi", "BT"), os = "macOS", mode = "APP")
    }
}

@Composable
fun DeviceDiscoveryCard(name: String, transports: List<String>, os: String, mode: String = "APP") {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        color = HybridSurface,
        shape = RoundedCornerShape(20.dp),
        border = BorderStroke(1.dp, Color.White.copy(0.05f))
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .background(HybridDark, CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Default.Computer,
                    contentDescription = null,
                    tint = HybridCyan,
                    modifier = Modifier.size(20.dp)
                )
            }
            Spacer(modifier = Modifier.width(16.dp))
            Column(modifier = Modifier.weight(1f)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(name, style = MaterialTheme.typography.titleMedium, color = TextPrimary, fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.width(8.dp))
                    ModeBadge(mode)
                }
                Text(os, style = MaterialTheme.typography.labelSmall, color = TextDim)
            }
            Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                transports.forEach { transport ->
                    TransportBadge(transport)
                }
            }
        }
    }
}

@Composable
fun ModeBadge(mode: String) {
    Surface(
        color = if (mode == "APP") HybridCyan.copy(0.1f) else Color.White.copy(0.1f),
        shape = RoundedCornerShape(4.dp),
    ) {
        Text(
            mode,
            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
            style = MaterialTheme.typography.labelSmall,
            color = if (mode == "APP") HybridCyan else Color.White.copy(0.6f),
            fontSize = 8.sp,
            fontWeight = FontWeight.Bold
        )
    }
}

@Composable
fun TransportBadge(label: String) {
    Surface(
        color = HybridCyan.copy(0.1f),
        shape = RoundedCornerShape(6.dp),
    ) {
        Text(
            label,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
            style = MaterialTheme.typography.labelSmall,
            color = HybridCyan,
            fontSize = 9.sp,
            fontWeight = FontWeight.ExtraBold
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
    onClick: () -> Unit
) {
    Surface(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth(),
        color = HybridSurface,
        shape = RoundedCornerShape(24.dp),
        border = AssistChipDefaults.assistChipBorder(borderColor = color.copy(alpha = 0.2f))
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
                    style = MaterialTheme.typography.titleLarge,
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

@Composable
private fun StatusItem(label: String, status: String, color: Color) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Box(
            modifier = Modifier
                .size(8.dp)
                .background(color, RoundedCornerShape(50))
        )
        Spacer(modifier = Modifier.width(8.dp))
        Column {
            Text(label, style = MaterialTheme.typography.labelSmall, color = TextSecondary)
            Text(status, style = MaterialTheme.typography.titleSmall, color = color, fontWeight = FontWeight.Bold)
        }
    }
}

val TextDim = Color(0xFF475569)