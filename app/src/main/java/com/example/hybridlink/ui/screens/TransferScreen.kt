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
import com.example.hybridlink.ui.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TransferScreen(navController: NavController, type: String) {
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
                    text = if (type == "send") "TRANSMITTING" else "RECEIVING",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = TextPrimary,
                    letterSpacing = 2.sp
                )
            }

            // File Info Card
            Surface(
                modifier = Modifier.fillMaxWidth(),
                color = HybridSurface,
                shape = RoundedCornerShape(24.dp),
                border = AssistChipDefaults.assistChipBorder(borderColor = Color.White.copy(0.05f))
            ) {
                Column(modifier = Modifier.padding(24.dp)) {
                    Text(
                        text = "system32_backup.iso",
                        style = MaterialTheme.typography.headlineSmall,
                        fontWeight = FontWeight.Bold,
                        color = TextPrimary
                    )
                    Text(
                        text = "4.2 GB • Multipath Enabled",
                        style = MaterialTheme.typography.bodyMedium,
                        color = TextSecondary
                    )
                    
                    Spacer(modifier = Modifier.height(32.dp))

                    // Progress Section
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.Bottom
                    ) {
                        Text(
                            text = "45%",
                            style = MaterialTheme.typography.displayMedium,
                            fontWeight = FontWeight.ExtraBold,
                            color = HybridCyan,
                            fontFamily = androidx.compose.ui.text.font.FontFamily.Monospace
                        )
                        Text(
                            text = "EST. 12m 40s",
                            style = MaterialTheme.typography.titleSmall,
                            color = TextSecondary,
                            modifier = Modifier.padding(bottom = 8.dp)
                        )
                    }
                    
                    Spacer(modifier = Modifier.height(12.dp))
                    
                    LinearProgressIndicator(
                        progress = 0.45f,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(12.dp),
                        color = HybridCyan,
                        trackColor = HybridSecondary,
                        strokeCap = androidx.compose.ui.graphics.StrokeCap.Round
                    )
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            // Speed Metrics Grid
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                SpeedCard(
                    label = "USB LINK",
                    speed = "24.5",
                    color = HybridCyan,
                    modifier = Modifier.weight(1f)
                )
                SpeedCard(
                    label = "WIFI LINK",
                    speed = "12.8",
                    color = HybridPurple,
                    modifier = Modifier.weight(1f)
                )
            }

            Spacer(modifier = Modifier.height(16.dp))
            
            // Advanced Scheduling Metrics
            SchedulingMetricsCard(parallelism = 4, health = 0.98f)

            Spacer(modifier = Modifier.weight(1f))

            // Controls
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                Button(
                    onClick = { /* TODO */ },
                    modifier = Modifier
                        .weight(1f)
                        .height(64.dp),
                    shape = RoundedCornerShape(16.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = HybridSecondary)
                ) {
                    Icon(Icons.Filled.Pause, contentDescription = null)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("PAUSE")
                }
                
                Button(
                    onClick = { navController.popBackStack() },
                    modifier = Modifier
                        .weight(1f)
                        .height(64.dp),
                    shape = RoundedCornerShape(16.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = AccentError.copy(0.1f)),
                    border = AssistChipDefaults.assistChipBorder(borderColor = AccentError.copy(0.2f))
                ) {
                    Text("CANCEL", color = AccentError, fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

@Composable
private fun SpeedCard(label: String, speed: String, color: Color, modifier: Modifier) {
    Surface(
        modifier = modifier,
        color = HybridSurface,
        shape = RoundedCornerShape(20.dp),
        border = AssistChipDefaults.assistChipBorder(borderColor = color.copy(0.1f))
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(label, style = MaterialTheme.typography.labelSmall, color = TextSecondary)
            Row(verticalAlignment = Alignment.Bottom) {
                Text(
                    text = speed,
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold,
                    color = color,
                    fontFamily = androidx.compose.ui.text.font.FontFamily.Monospace
                )
                Text(
                    text = " MB/s",
                    style = MaterialTheme.typography.labelSmall,
                    color = TextDim,
                    modifier = Modifier.padding(bottom = 4.dp, start = 2.dp)
                )
            }
        }
    }
}
