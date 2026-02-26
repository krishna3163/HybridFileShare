package com.example.hybridlink.ui.screens

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import com.example.hybridlink.ui.theme.*
import com.example.hybridlink.ui.viewmodels.MainViewModel
import com.example.hybridlink.util.DiscoveredDevice
import android.content.Intent
import android.widget.Toast
import androidx.compose.ui.platform.LocalContext
import kotlinx.coroutines.delay

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun NearbyShareScreen(navController: NavController, viewModel: MainViewModel) {
    val discoveredDevices by viewModel.discoveredDevices.collectAsState()
    val isWebShare = viewModel.isWebShareEnabled
    val context = LocalContext.current
    var showQRDialog by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        viewModel.startDiscovery()
    }
    
    DisposableEffect(Unit) {
        onDispose {
            viewModel.stopDiscovery()
        }
    }

    if (showQRDialog) {
        AlertDialog(
            onDismissRequest = { showQRDialog = false },
            title = { Text("QR Pairing", color = TextPrimary) },
            text = {
                Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.fillMaxWidth()) {
                    Box(
                        modifier = Modifier.size(200.dp).background(Color.White, RoundedCornerShape(12.dp)),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(Icons.Filled.QrCode, contentDescription = null, modifier = Modifier.size(160.dp), tint = HybridDark)
                    }
                    Spacer(modifier = Modifier.height(16.dp))
                    Text("Scan to connect instantly", color = TextSecondary, fontSize = 14.sp)
                }
            },
            confirmButton = {
                TextButton(onClick = { showQRDialog = false }) {
                    Text("CLOSE", color = HybridCyan)
                }
            },
            containerColor = HybridSurface,
            shape = RoundedCornerShape(24.dp)
        )
    }
    
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(HybridDark)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp)
        ) {
            // Header
            Row(
                modifier = Modifier.fillMaxWidth().padding(bottom = 24.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                IconButton(
                    onClick = { navController.popBackStack() },
                    colors = IconButtonDefaults.iconButtonColors(containerColor = HybridSecondary)
                ) {
                    Icon(Icons.Filled.ArrowBack, contentDescription = "Back", tint = TextPrimary)
                }
                Spacer(modifier = Modifier.width(16.dp))
                Text(
                    text = "NEARBY DISCOVERY",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = TextPrimary,
                    letterSpacing = 2.sp
                )
            }

            // Radar Section
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(260.dp),
                contentAlignment = Alignment.Center
            ) {
                RadarAnimation()
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Icon(
                        if (isWebShare) Icons.Filled.CloudUpload else Icons.Filled.WifiTethering,
                        contentDescription = null,
                        modifier = Modifier.size(64.dp),
                        tint = if (isWebShare) HybridCyan else TextDim
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    Text(
                        if (isWebShare) "WEB BROADCASTING" else "SCANNING FOR PEERS",
                        color = if (isWebShare) HybridCyan else TextDim,
                        style = MaterialTheme.typography.labelSmall,
                        fontWeight = FontWeight.ExtraBold,
                        letterSpacing = 2.sp
                    )
                }
            }

            // Tools Row
            Row(
                modifier = Modifier.fillMaxWidth().padding(vertical = 16.dp),
                horizontalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                FeatureToggleCard(
                    title = "Web Share",
                    enabled = isWebShare,
                    icon = Icons.Filled.Language,
                    modifier = Modifier.weight(1f),
                    onClick = { viewModel.toggleWebShare() }
                )
                FeatureToggleCard(
                    title = "QR Pairing",
                    enabled = showQRDialog,
                    icon = Icons.Filled.QrCodeScanner,
                    modifier = Modifier.weight(1f),
                    onClick = { showQRDialog = true }
                )
            }

            Text(
                "DISCOVERED DEVICES",
                style = MaterialTheme.typography.labelMedium,
                color = TextDim,
                letterSpacing = 1.5.sp,
                modifier = Modifier.padding(bottom = 16.dp, top = 8.dp)
            )

            if (discoveredDevices.isEmpty()) {
                Box(modifier = Modifier.weight(1f).fillMaxWidth(), contentAlignment = Alignment.Center) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        CircularProgressIndicator(modifier = Modifier.size(24.dp), color = HybridCyan, strokeWidth = 2.dp)
                        Spacer(modifier = Modifier.height(16.dp))
                        Text("Searching for peer engines...", color = TextDim, fontSize = 14.sp)
                    }
                }
            } else {
                LazyColumn(
                    modifier = Modifier.weight(1f).fillMaxWidth(),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    items(discoveredDevices) { device ->
                        DeviceCard(device) {
                            // Launch ClientActivity and fill IP
                            val intent = Intent(context, top.weixiansen574.hybridfilexfer.ClientActivity::class.java)
                            intent.putExtra("auto_connect_ip", device.host)
                            context.startActivity(intent)
                            Toast.makeText(context, "Connecting to ${device.name}...", Toast.LENGTH_SHORT).show()
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun RadarAnimation() {
    val infiniteTransition = rememberInfiniteTransition()
    val radius by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 400f,
        animationSpec = infiniteRepeatable(
            animation = tween(2500, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        )
    )
    val alpha by infiniteTransition.animateFloat(
        initialValue = 0.6f,
        targetValue = 0f,
        animationSpec = infiniteRepeatable(
            animation = tween(2500, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        )
    )

    Canvas(modifier = Modifier.fillMaxSize()) {
        drawCircle(
            color = HybridCyan.copy(alpha = alpha),
            radius = radius,
            style = Stroke(width = 2.dp.toPx())
        )
        drawCircle(
            color = HybridCyan.copy(alpha = alpha * 0.5f),
            radius = radius / 2f,
            style = Stroke(width = 2.dp.toPx())
        )
    }
}

@Composable
fun DeviceCard(device: DiscoveredDevice, onClick: () -> Unit) {
    Surface(
        onClick = onClick,
        color = HybridSecondary,
        shape = RoundedCornerShape(20.dp),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier.size(44.dp).background(HybridCyan.copy(alpha = 0.2f), CircleShape),
                contentAlignment = Alignment.Center
            ) {
                val icon = when (device.platform.lowercase()) {
                    "android" -> Icons.Filled.Smartphone
                    "win32", "windows" -> Icons.Filled.Computer
                    "web" -> Icons.Filled.Language
                    else -> Icons.Filled.DeviceUnknown
                }
                Icon(icon, contentDescription = null, tint = HybridCyan)
            }
            Spacer(modifier = Modifier.width(16.dp))
            Column {
                Text(device.name, fontWeight = FontWeight.Bold, color = TextPrimary)
                val typeLabel = when (device.platform.lowercase()) {
                    "android" -> "Android Node"
                    "win32" -> "Windows Node"
                    "web" -> "Web Dashboard"
                    else -> "HybridLink Node"
                }
                Text("$typeLabel • ${device.host}", fontSize = 12.sp, color = TextDim)
            }
            Spacer(modifier = Modifier.weight(1f))
            Icon(Icons.Filled.ChevronRight, contentDescription = null, tint = TextDim)
        }
    }
}

@Composable
fun FeatureToggleCard(title: String, enabled: Boolean, icon: ImageVector, modifier: Modifier, onClick: () -> Unit) {
    Surface(
        onClick = onClick,
        color = if (enabled) HybridCyan.copy(alpha = 0.1f) else HybridSecondary,
        shape = RoundedCornerShape(20.dp),
        border = if (enabled) androidx.compose.foundation.BorderStroke(1.dp, HybridCyan.copy(alpha = 0.3f)) else null,
        modifier = modifier
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(icon, contentDescription = null, tint = if (enabled) HybridCyan else TextDim)
            Spacer(modifier = Modifier.height(8.dp))
            Text(title, fontWeight = FontWeight.Bold, color = if (enabled) HybridCyan else TextPrimary, fontSize = 12.sp)
        }
    }
}
