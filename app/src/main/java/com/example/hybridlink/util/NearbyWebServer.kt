package com.example.hybridlink.util

import android.content.Context
import android.net.Uri
import android.util.Log
import top.weixiansen574.hybridfilexfer.core.Utils
import top.weixiansen574.hybridfilexfer.droidcore.HFXServer
import java.io.*
import java.net.ServerSocket
import java.net.Socket
import java.net.URLDecoder
import kotlin.concurrent.thread

class NearbyWebServer(private val context: Context, private val hfxServer: HFXServer?) {
    private var serverSocket: ServerSocket? = null
    private var isRunning = false

    fun start(port: Int) {
        if (isRunning) return
        isRunning = true
        thread {
            try {
                serverSocket = ServerSocket(port)
                Log.d("WebShare", "Server started on port $port")
                while (isRunning) {
                    val client = serverSocket?.accept() ?: break
                    handleClient(client)
                }
            } catch (e: Exception) {
                Log.e("WebShare", "Server error", e)
            } finally {
                isRunning = false
            }
        }
    }

    fun stop() {
        isRunning = false
        serverSocket?.close()
        serverSocket = null
    }

    private fun handleClient(socket: Socket) {
        thread {
            try {
                val input = BufferedReader(InputStreamReader(socket.getInputStream()))
                val output = PrintWriter(socket.getOutputStream())
                
                val requestLine = input.readLine() ?: return@thread
                Log.d("WebShare", "Request: $requestLine")
                
                val parts = requestLine.split(" ")
                if (parts.size < 2) return@thread
                
                val path = URLDecoder.decode(parts[1], "UTF-8")
                
                if (path == "/" || path == "/index.html") {
                    sendResponse(output, "text/html", getIndexHtml())
                } else if (path.startsWith("/download/")) {
                    val fileName = path.removePrefix("/download/")
                    handleDownload(socket, fileName)
                } else {
                    sendResponse(output, "text/plain", "404 Not Found", "404 Not Found")
                }
                
                socket.close()
            } catch (e: Exception) {
                Log.e("WebShare", "Client handling error", e)
            }
        }
    }

    private fun sendResponse(out: PrintWriter, contentType: String, content: String, status: String = "200 OK") {
        out.println("HTTP/1.1 $status")
        out.println("Content-Type: $contentType")
        out.println("Content-Length: ${content.length}")
        out.println("Connection: close")
        out.println()
        out.print(content)
        out.flush()
    }

    private fun handleDownload(socket: Socket, fileName: String) {
        // This is a placeholder for actual file streaming 
        // In a real implementation, we would use HFXServer/IOService to read the file
        val output = socket.getOutputStream()
        val header = "HTTP/1.1 200 OK\r\n" +
                     "Content-Type: application/octet-stream\r\n" +
                     "Content-Disposition: attachment; filename=\"$fileName\"\r\n" +
                     "Connection: close\r\n\r\n"
        output.write(header.toByteArray())
        output.write("File content would go here. For full support, use the HybridLink app.".toByteArray())
        output.flush()
    }

    private fun getIndexHtml(): String {
        return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>HybridLink Web Share</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body { font-family: sans-serif; background: #0f172a; color: white; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
                    .card { background: #1e293b; padding: 2rem; border-radius: 1.5rem; box-shadow: 0 10px 25px rgba(0,0,0,0.5); text-align: center; max-width: 90%; }
                    h1 { color: #22d3ee; margin-top: 0; }
                    .btn { background: #22d3ee; color: #0f172a; border: none; padding: 1rem 2rem; border-radius: 0.75rem; font-weight: bold; cursor: pointer; text-decoration: none; display: inline-block; margin-top: 1rem; }
                    .info { color: #94a3b8; font-size: 0.875rem; margin-top: 1rem; }
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>HYBRIDLINK</h1>
                    <p>You are connected to a Nearby HybridLink Host.</p>
                    <p>To experience <b>Multipath High-Speed</b> transfers, please download the Android app.</p>
                    <a href="#" class="btn">DOWNLOAD APP</a>
                    <div class="info">Web fallback is limited to single-stream.</div>
                </div>
            </body>
            </html>
        """.trimIndent()
    }
}
