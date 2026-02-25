package com.example.hybridlink.ui.theme

import android.app.Activity
import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val HybridColorScheme = darkColorScheme(
    primary = HybridCyan,
    secondary = HybridPurple,
    tertiary = HybridCyan,
    background = HybridDark,
    surface = HybridSurface,
    onPrimary = HybridDark,
    onSecondary = HybridDark,
    onTertiary = HybridDark,
    onBackground = TextPrimary,
    onSurface = TextPrimary,
    surfaceVariant = HybridSecondary,
    onSurfaceVariant = TextSecondary
)

@Composable
fun HybridLinkTheme(
    darkTheme: Boolean = true, // Force dark theme for that premium look
    dynamicColor: Boolean = false, // Disable dynamic color to maintain brand identity
    content: @Composable () -> Unit
) {
    val colorScheme = HybridColorScheme
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = HybridDark.toArgb()
            window.navigationBarColor = HybridDark.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = false
        }
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}
