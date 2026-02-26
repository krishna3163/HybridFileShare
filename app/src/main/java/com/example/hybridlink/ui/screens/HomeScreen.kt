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
import android.content.Intent
import androidx.hilt.navigation.compose.hiltViewModel
import kotlinx.coroutines.delay

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(navController: NavController, viewModel: com.example.hybridlink.ui.viewmodels.MainViewModel = hiltViewModel()) {
    val context = androidx.compose.ui.platform.LocalContext.current
    
    val isServerRunning = viewModel.isServerRunning
    val serverStatusText = viewModel.serverStatusText
    val accessMode = viewModel.accessMode
    
    val scrollState = rememberScrollState()

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
                modifier = Modifier.fillMaxWidth().padding(bottom = 24.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    androidx.compose.foundation.Image(
                        painter = androidx.compose.ui.res.painterResource(id = com.example.hybridlink.R.drawable.logo),
                        contentDescription = "Logo",
                        modifier = Modifier
                            .size(54.dp)
                            .clip(RoundedCornerShape(12.dp))
                            .background(Color.White.copy(alpha = 0.05f))
                            .padding(8.dp)
                    )
                    Spacer(modifier = Modifier.width(16.dp))
                    Column {
                        Text(
                            text = "HybridFileShare",
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.ExtraBold,
                            color = TextPrimary,
                            letterSpacing = (-0.5).sp
                        )
                        Text(
                            text = "EXTREME ENGINE",
                            style = MaterialTheme.typography.labelSmall,
                            color = HybridCyan,
                            letterSpacing = 2.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
                Row(verticalAlignment = Alignment.CenterVertically) {
                    IconButton(
                        onClick = { viewModel.toggleWebShare() },
                        colors = IconButtonDefaults.iconButtonColors(containerColor = if (viewModel.isWebShareEnabled) HybridCyan.copy(alpha=0.2f) else HybridSecondary)
                    ) {
                        Icon(Icons.Filled.Public, contentDescription = "Web Share", tint = if (viewModel.isWebShareEnabled) HybridCyan else TextPrimary)
                    }
                    Spacer(modifier = Modifier.width(8.dp))
                    IconButton(
                        onClick = { navController.navigate("settings") },
                        colors = IconButtonDefaults.iconButtonColors(containerColor = HybridSecondary)
                    ) {
                        Icon(Icons.Filled.Settings, contentDescription = "Settings", tint = TextPrimary)
                    }
                }
            }

            // --- SERVER CONTROL CARD ---
            Card(
                modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp),
                colors = CardDefaults.cardColors(containerColor = if (isServerRunning) HybridCyan.copy(alpha=0.1f) else HybridSecondary),
                shape = RoundedCornerShape(24.dp),
                border = androidx.compose.foundation.BorderStroke(1.dp, if (isServerRunning) HybridCyan.copy(alpha=0.4f) else Color.White.copy(alpha=0.05f))
            ) {
                Column(modifier = Modifier.padding(24.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(modifier = Modifier
                            .size(10.dp)
                            .background(if (isServerRunning) HybridCyan else Color.Red, CircleShape)
                        )
                        Spacer(modifier = Modifier.width(10.dp))
                        Text(
                            text = if (isServerRunning) "ENGINE BROADCASTING" else "ENGINE OFFLINE",
                            color = if (isServerRunning) HybridCyan else Color.Red.copy(alpha=0.7f),
                            fontWeight = FontWeight.ExtraBold,
                            fontSize = 11.sp,
                            letterSpacing = 1.2.sp
                        )
                    }
                    Spacer(modifier = Modifier.height(12.dp))
                    Text(
                        serverStatusText, 
                        color = TextPrimary, 
                        fontSize = 20.sp, 
                        fontWeight = FontWeight.Bold,
                        lineHeight = 28.sp
                    )
                    
                    Spacer(modifier = Modifier.height(20.dp))
                    Button(
                        onClick = { viewModel.toggleServer() },
                        colors = ButtonDefaults.buttonColors(
                            containerColor = if (isServerRunning) HybridPurple else HybridCyan,
                            contentColor = if (isServerRunning) Color.White else HybridDark
                        ),
                        modifier = Modifier.fillMaxWidth().height(56.dp),
                        shape = RoundedCornerShape(16.dp),
                        elevation = ButtonDefaults.buttonElevation(defaultElevation = 0.dp)
                    ) {
                        Icon(if (isServerRunning) Icons.Filled.PowerSettingsNew else Icons.Filled.Bolt, contentDescription = null)
                        Spacer(modifier = Modifier.width(10.dp))
                        Text(if (isServerRunning) "STOP ENGINE" else "START HYBRID BOOST", fontWeight = FontWeight.ExtraBold, letterSpacing = 1.sp)
                    }
                }
            }

            // --- ACCESS MODE SELECTION ---
            Text(
                "SYSTEM PRIVILEGES",
                style = MaterialTheme.typography.labelMedium,
                color = TextDim,
                letterSpacing = 2.sp,
                modifier = Modifier.padding(top = 24.dp, bottom = 12.dp, start = 4.dp)
            )
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                ModeSelectionChip("USER", accessMode == "NORMAL", Icons.Filled.Person) { viewModel.accessMode = "NORMAL" }
                ModeSelectionChip("ADB", accessMode == "SHIZUKU", Icons.Filled.Terminal) { viewModel.accessMode = "SHIZUKU" }
                ModeSelectionChip("ROOT", accessMode == "ROOT", Icons.Filled.Security) { viewModel.accessMode = "ROOT" }
            }

            // --- NETWORK CHANNELS SELECTION ---
            Text(
                "ACTIVE INTERFACES",
                style = MaterialTheme.typography.labelMedium,
                color = TextDim,
                letterSpacing = 2.sp,
                modifier = Modifier.padding(top = 28.dp, bottom = 12.dp, start = 4.dp)
            )
            
            Surface(
                color = HybridSecondary.copy(alpha=0.5f),
                shape = RoundedCornerShape(24.dp),
                border = androidx.compose.foundation.BorderStroke(1.dp, Color.White.copy(alpha=0.05f))
            ) {
                Column(modifier = Modifier.padding(vertical = 8.dp)) {
                    viewModel.networkInterfaces.forEachIndexed { index, item ->
                        ChannelToggleRow(
                            title = item.name,
                            ip = item.address,
                            status = item.state,
                            checked = item.isEnabled,
                            onCheckedChange = { 
                                viewModel.networkInterfaces[index] = item.copy(isEnabled = it)
                            }
                        )
                        if (index < viewModel.networkInterfaces.size - 1) {
                            Divider(color = Color.White.copy(alpha = 0.05f), modifier = Modifier.padding(horizontal = 16.dp))
                        }
                    }
                    if (viewModel.networkInterfaces.isEmpty()) {
                        Text("Searching for interfaces...", color = TextDim, modifier = Modifier.padding(24.dp), fontSize = 14.sp)
                    }
                }
            }
            
            Spacer(modifier = Modifier.height(32.dp))

            // --- QUICK ACTIONS ---
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                ActionCard(
                    title = "Nearby Discovery",
                    subtitle = "Find and connect to nearby peers",
                    icon = Icons.Filled.Radar,
                    color = HybridCyan,
                    onClick = { 
                        navController.navigate("nearby")
                    }
                )
                ActionCard(
                    title = "File Transfer Manager",
                    subtitle = "Dual-pane file explorer & transfer",
                    icon = Icons.Filled.CompareArrows,
                    color = HybridCyan,
                    onClick = { 
                        if (isServerRunning) {
                            context.startActivity(Intent(context, top.weixiansen574.hybridfilexfer.TransferActivity::class.java))
                        } else {
                            android.widget.Toast.makeText(context, "Please start the Engine first!", android.widget.Toast.LENGTH_SHORT).show()
                        }
                    }
                )
                ActionCard(
                    title = "Connect to Remote Peer",
                    subtitle = "Join an existing transfer session",
                    icon = Icons.Filled.Input,
                    color = Color(0xFF60A5FA),
                    onClick = { 
                        context.startActivity(Intent(context, top.weixiansen574.hybridfilexfer.ClientActivity::class.java))
                    }
                )
                ActionCard(
                    title = "Library & Bookmarks",
                    subtitle = "Quick access to your saved paths",
                    icon = Icons.Filled.AutoAwesomeMotion,
                    color = HybridPurple,
                    onClick = { 
                        // Show a placeholder message since we don't have a BookmarksActivity yet
                        android.widget.Toast.makeText(context, "Bookmarks loading...", android.widget.Toast.LENGTH_SHORT).show()
                    }
                )
            }
            Spacer(modifier = Modifier.height(48.dp))
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
fun ChannelToggleRow(title: String, ip: String, status: String, checked: Boolean, onCheckedChange: (Boolean) -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(title, color = TextPrimary, fontWeight = FontWeight.Medium, fontSize = 14.sp)
                Spacer(modifier = Modifier.width(8.dp))
                Text(status, color = if (status == "Connected") HybridCyan else TextDim, fontSize = 10.sp, fontWeight = FontWeight.Bold)
            }
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
        modifier = Modifier
            .fillMaxWidth()
            .alpha(if (enabled) 1f else 0.5f)
            .height(88.dp),
        color = Color.White.copy(alpha = 0.03f),
        shape = RoundedCornerShape(24.dp),
        border = androidx.compose.foundation.BorderStroke(
            1.dp, 
            Brush.linearGradient(
                listOf(Color.White.copy(alpha = 0.15f), Color.Transparent, color.copy(alpha = 0.2f))
            )
        ),
        enabled = enabled
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 20.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(48.dp)
                    .background(
                        Brush.radialGradient(
                            listOf(color.copy(alpha = 0.2f), color.copy(alpha = 0.05f))
                        ), 
                        RoundedCornerShape(14.dp)
                    ),
                contentAlignment = Alignment.Center
            ) {
                Icon(icon, contentDescription = null, tint = color, modifier = Modifier.size(24.dp))
            }
            Spacer(modifier = Modifier.width(20.dp))
            Column {
                Text(
                    text = title,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.ExtraBold,
                    color = TextPrimary,
                    fontSize = 16.sp,
                    letterSpacing = 0.5.sp
                )
                Text(
                    text = subtitle,
                    style = MaterialTheme.typography.bodySmall,
                    color = TextDim,
                    fontSize = 12.sp
                )
            }
            Spacer(modifier = Modifier.weight(1f))
            Icon(Icons.Filled.ArrowForwardIos, contentDescription = null, tint = TextDim.copy(alpha=0.5f), modifier = Modifier.size(14.dp))
        }
    }
}

val TextDim = Color(0xFF475569)