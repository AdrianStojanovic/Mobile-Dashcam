import android.util.Log
import kotlinx.coroutines.*
import okhttp3.*
import okio.ByteString
import java.util.concurrent.TimeUnit
import kotlin.math.pow
import com.adrian.tsr_app.WebSocketCallback

class WebSocketManager(
    private val url: String,
    private val listener: MyWebSocketListener,
    private val callback: WebSocketCallback
) {
    private val client = OkHttpClient()
    private var webSocket: WebSocket? = null
    private var job: Job? = null
    private var reconnectAttempts = 0
    private val maxReconnectAttempts = 5
    private val baseReconnectDelay = 0L

    fun connect() {
        job = GlobalScope.launch {
            val request = Request.Builder().url(url).build()
            webSocket = client.newWebSocket(request, object : WebSocketListener() {
                override fun onOpen(webSocket: WebSocket, response: Response) {
                    println("WebSocket connected!")
                    reconnectAttempts = 0
                }

                override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                    Log.e("websocket error", "websocket error: ${t.message}")
                    attemptReconnect()
                }

                override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                    attemptReconnect()
                }

                override fun onMessage(webSocket: WebSocket, text: String) {
                    Log.d("websocket", "websocket received message: $text")
                    callback.onMessageReceived(text)
                }
            })
        }
    }


    fun sendMessage(message: String) {
        webSocket?.send(message) ?: Log.e("websocket error", "websocket not connected")
    }

    fun sendBinaryData(header: String, byteArray: ByteArray) {
        if (header.length != 10) {
            return
        }

        val headerBytes = header.toByteArray(Charsets.UTF_8)
        val combinedBytes = headerBytes + byteArray

        val byteString = ByteString.of(*combinedBytes)
        webSocket?.send(byteString) ?: Log.e("websocket error", "websocket not connected")
    }


    private fun attemptReconnect() {
        if (reconnectAttempts < maxReconnectAttempts) {
            val delay = baseReconnectDelay * (2.0.pow(reconnectAttempts.toDouble())).toLong()
            reconnectAttempts++
            Log.d("websocket", "trying to reconnect...")

            GlobalScope.launch {
                delay(delay)
                connect()
            }
        } else {
            Log.d("websocket", "reached max amount of reconnect attempts")
        }
    }


    fun close() {
        webSocket?.close(1000, "Manuell geschlossen")
        client.dispatcher.executorService.shutdown()
        job?.cancel()
    }
}
