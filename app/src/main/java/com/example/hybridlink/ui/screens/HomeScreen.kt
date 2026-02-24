package com.example.hybridlink.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController

@Composable
fun HomeScreen(navController: NavController) {
    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Button(onClick = { /* TODO: Implement send file logic */ }) {
            Text("Send File")
        }
        Spacer(modifier = Modifier.height(16.dp))
        Button(onClick = { /* TODO: Implement receive file logic */ }) {
            Text("Receive File")
        }
        Spacer(modifier = Modifier.height(32.dp))
        Text("USB: Connected") // TODO: Get actual status
        Text("WiFi: Disconnected") // TODO: Get actual status
    }
}
