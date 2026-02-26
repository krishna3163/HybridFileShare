package com.example.hybridlink.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
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
import com.example.hybridlink.ui.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HelpScreen(navController: NavController) {
    val scrollState = rememberScrollState()

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(HybridDark)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp)
                .verticalScroll(scrollState)
        ) {
            // Top Bar
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 32.dp),
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
                    text = "APPLICATION HELP",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = TextPrimary,
                    letterSpacing = 2.sp
                )
            }

            HelpSection(
                title = "Multipath Transfer",
                icon = Icons.Filled.MultipleStop,
                content = "HybridLink uses multiple network paths simultaneously. You can enable WiFi, USB Tethering, and ADB Forwarding at the same time to achieve aggregate speeds far exceeding a single connection."
            )

            HelpSection(
                title = "Access Modes",
                icon = Icons.Filled.Security,
                content = "• NORMAL: Accesses Standard internal storage.\n" +
                          "• SHIZUKU: Uses Shizuku to access protected app data (/Android/data) without Root.\n" +
                          "• ROOT: Full system-level access for rooted devices."
            )

            HelpSection(
                title = "USB ADB Channel",
                icon = Icons.Filled.Usb,
                content = "To use the USB ADB channel, ensure 'Wireless Debugging' or 'USB Debugging' is enabled on your device. On your PC, use 'adb forward tcp:9000 tcp:9000' to create the bridge."
            )

            HelpSection(
                title = "Native Memory Engine",
                icon = Icons.Filled.Memory,
                content = "The OOM-resistant engine utilizes high-performance C++ JNI buffers. If you experience crashes on devices with low RAM, reduce the 'Buffer Block Count' in settings."
            )

            Spacer(modifier = Modifier.height(32.dp))
            
            Text(
                "Version 1.2.0-Alpha • HybridLink Multipath",
                color = TextDim,
                fontSize = 12.sp,
                modifier = Modifier.align(Alignment.CenterHorizontally)
            )
        }
    }
}

@Composable
private fun HelpSection(title: String, icon: ImageVector, content: String) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .padding(bottom = 16.dp),
        color = HybridSurface,
        shape = RoundedCornerShape(24.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, HybridCyan.copy(alpha = 0.1f))
    ) {
        Row(modifier = Modifier.padding(20.dp)) {
            Icon(icon, contentDescription = null, tint = HybridCyan, modifier = Modifier.size(24.dp))
            Spacer(modifier = Modifier.width(16.dp))
            Column {
                Text(
                    text = title.uppercase(),
                    style = MaterialTheme.typography.labelLarge,
                    fontWeight = FontWeight.Bold,
                    color = TextPrimary,
                    letterSpacing = 1.sp
                )
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = content,
                    style = MaterialTheme.typography.bodyMedium,
                    color = TextSecondary,
                    lineHeight = 20.sp
                )
            }
        }
    }
}
