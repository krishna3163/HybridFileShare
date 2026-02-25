package com.example.hybridlink.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import com.example.hybridlink.ui.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(navController: NavController) {
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
                    text = "CONFIGURATION",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = TextPrimary,
                    letterSpacing = 2.sp
                )
            }

            // Settings Group
            Surface(
                modifier = Modifier.fillMaxWidth(),
                color = HybridSurface,
                shape = RoundedCornerShape(24.dp),
                border = AssistChipDefaults.assistChipBorder(borderColor = Color.White.copy(0.05f))
            ) {
                Column(modifier = Modifier.padding(24.dp), verticalArrangement = Arrangement.spacedBy(20.dp)) {
                    SettingInput(
                        label = "Chunk Size (MB)",
                        value = "4",
                        placeholder = "e.g. 4"
                    )
                    
                    SettingInput(
                        label = "Default WiFi Port",
                        value = "9001",
                        placeholder = "e.g. 8080"
                    )

                    HorizontalDivider(color = Color.White.copy(0.05f))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text("Auto Resume", style = MaterialTheme.typography.titleMedium, color = TextPrimary)
                            Text("Restart interrupted links", style = MaterialTheme.typography.bodySmall, color = TextSecondary)
                        }
                        Switch(
                            checked = true, 
                            onCheckedChange = {},
                            colors = SwitchDefaults.colors(
                                checkedThumbColor = HybridDark,
                                checkedTrackColor = HybridCyan,
                                uncheckedBorderColor = Color.White.copy(0.2f)
                            )
                        )
                    }
                }
            }
            
            Spacer(modifier = Modifier.weight(1f))
            
            Text(
                text = "HybridLink Engine v1.2.0-stable",
                modifier = Modifier.align(Alignment.CenterHorizontally),
                style = MaterialTheme.typography.labelSmall,
                color = TextDim
            )
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun SettingInput(label: String, value: String, placeholder: String) {
    Column {
        Text(
            text = label,
            style = MaterialTheme.typography.labelMedium,
            color = TextSecondary,
            modifier = Modifier.padding(bottom = 8.dp)
        )
        TextField(
            value = value,
            onValueChange = {},
            modifier = Modifier.fillMaxWidth(),
            colors = TextFieldDefaults.textFieldColors(
                containerColor = HybridSecondary,
                focusedIndicatorColor = HybridCyan,
                unfocusedIndicatorColor = Color.Transparent,
                textColor = TextPrimary
            ),
            shape = RoundedCornerShape(12.dp)
        )
    }
}
