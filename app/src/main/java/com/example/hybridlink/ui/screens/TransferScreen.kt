package com.example.hybridlink.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.width
import androidx.compose.material3.Button
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController

@Composable
fun TransferScreen(navController: NavController) {
    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text("Transferring file...")
        Spacer(modifier = Modifier.height(16.dp))
        LinearProgressIndicator(progress = 0.5f) // TODO: Get actual progress
        Spacer(modifier = Modifier.height(16.dp))
        Row {
            Text("USB: 10 MB/s") // TODO: Get actual speed
            Spacer(modifier = Modifier.width(16.dp))
            Text("WiFi: 5 MB/s") // TODO: Get actual speed
        }
        Spacer(modifier = Modifier.height(32.dp))
        Row {
            Button(onClick = { /* TODO: Implement pause logic */ }) {
                Text("Pause")
            }
            Spacer(modifier = Modifier.width(16.dp))
            Button(onClick = { /* TODO: Implement cancel logic */ }) {
                Text("Cancel")
            }
        }
    }
}
