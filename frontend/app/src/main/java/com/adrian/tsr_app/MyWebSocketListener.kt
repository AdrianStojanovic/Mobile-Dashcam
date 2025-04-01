import android.util.Log
import com.adrian.tsr_app.WebSocketCallback
import okhttp3.*
import okio.ByteString

class MyWebSocketListener(private val callback: WebSocketCallback) : WebSocketListener() {

    override fun onOpen(webSocket: WebSocket, response: Response) {
        Log.d("WebSocket", "WebSocket Connected")
    }

    override fun onMessage(webSocket: WebSocket, text: String) {
        Log.d("websocket", "received message: $text")
        callback.onMessageReceived(text)
    }

    override fun onMessage(webSocket: WebSocket, bytes: ByteString) {
        val message = bytes.utf8()
        Log.d("websocket", "received binary message: $message")
        callback.onMessageReceived(message)
    }

    override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
        Log.e("WebSocket", "error: " + t.message)
        callback.onError(t.message ?: "unknown error")
    }
}
