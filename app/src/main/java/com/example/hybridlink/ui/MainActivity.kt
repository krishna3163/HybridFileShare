package com.example.hybridlink.ui
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.provider.Settings
import android.content.pm.PackageManager

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.example.hybridlink.ui.screens.HelpScreen
import com.example.hybridlink.ui.screens.HomeScreen
import com.example.hybridlink.ui.screens.SettingsScreen
import com.example.hybridlink.ui.screens.TransferScreen
import com.example.hybridlink.ui.screens.NearbyShareScreen
import com.example.hybridlink.ui.theme.HybridLinkTheme
import androidx.hilt.navigation.compose.hiltViewModel
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    private val permissions = arrayOf(
        android.Manifest.permission.INTERNET,
        android.Manifest.permission.ACCESS_NETWORK_STATE,
        android.Manifest.permission.ACCESS_WIFI_STATE,
        android.Manifest.permission.READ_EXTERNAL_STORAGE,
        android.Manifest.permission.WRITE_EXTERNAL_STORAGE,
        android.Manifest.permission.ACCESS_FINE_LOCATION,
        android.Manifest.permission.ACCESS_COARSE_LOCATION
    )

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        requestPermissions()
        
        setContent {
            HybridLinkTheme {
                // A surface container using the 'background' color from the theme
                Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
                    val viewModel: com.example.hybridlink.ui.viewmodels.MainViewModel = hiltViewModel()
                    MainNavigation(viewModel)
                }
            }
        }
    }

    private fun requestPermissions() {
        val list = mutableListOf<String>()
        for (permission in permissions) {
            if (checkSelfPermission(permission) != PackageManager.PERMISSION_GRANTED) {
                list.add(permission)
            }
        }
        if (list.isNotEmpty()) {
            requestPermissions(list.toTypedArray(), 1)
        }
        
        // Special case for MANAGE_EXTERNAL_STORAGE (Android 11+)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            if (!Environment.isExternalStorageManager()) {
                val intent = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION)
                val uri = Uri.fromParts("package", packageName, null)
                intent.data = uri
                startActivity(intent)
            }
        }
    }
}

@Composable
fun MainNavigation(viewModel: com.example.hybridlink.ui.viewmodels.MainViewModel) {
    val navController = rememberNavController()
    NavHost(navController = navController, startDestination = "home") {
        composable("home") { HomeScreen(navController, viewModel) }
        composable(
            "transfer/{type}",
            arguments = listOf(navArgument("type") { type = NavType.StringType })
        ) { backStackEntry ->
            val type = backStackEntry.arguments?.getString("type") ?: ""
            TransferScreen(navController, type)
        }
        composable("settings") { SettingsScreen(navController) }
        composable("help") { HelpScreen(navController) }
        composable("nearby") { NearbyShareScreen(navController, viewModel) }
    }
}

@Preview(showBackground = true)
@Composable
fun DefaultPreview() {
    HybridLinkTheme {
        // Preview won't work perfectly with Hilt, but we fix the signature
        Surface {
            // In a real preview we would use a mock ViewModel
        }
    }
}
