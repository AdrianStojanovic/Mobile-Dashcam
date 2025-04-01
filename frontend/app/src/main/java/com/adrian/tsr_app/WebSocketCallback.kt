package com.adrian.tsr_app

interface WebSocketCallback {
    fun onMessageReceived(message: String)
    fun onError(error: String)
}