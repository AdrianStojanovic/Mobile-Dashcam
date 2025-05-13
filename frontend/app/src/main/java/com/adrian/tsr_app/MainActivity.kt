package com.adrian.tsr_app

import MyWebSocketListener
import WebSocketManager
import android.Manifest
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.Matrix
import android.os.Bundle
import android.util.Log
import android.widget.ImageView
import android.widget.LinearLayout
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.core.AspectRatio
import androidx.camera.core.Camera
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.adrian.tsr_app.databinding.ActivityMainBinding
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import android.widget.Toast
import androidx.lifecycle.Observer
import androidx.activity.viewModels
import org.json.JSONArray
import java.io.ByteArrayOutputStream

class MainActivity : AppCompatActivity(), WebSocketCallback {
    private lateinit var binding: ActivityMainBinding
    private val isFrontCamera = false

    private var preview: Preview? = null
    private var imageAnalyzer: ImageAnalysis? = null
    private var camera: Camera? = null
    private var cameraProvider: ProcessCameraProvider? = null
    private val temporarySigns: TemporarySigns by viewModels()
    private lateinit var webSocketManager: WebSocketManager
    private var nightMode: String = "normalmode"

    private val signTimestamps = mutableMapOf<String, Long>()
    private val displayedImages = mutableMapOf<String, ImageView>()
    private val signDisplayDuration = 2000L

    private lateinit var cameraExecutor: ExecutorService

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        val button = binding.nightmodeButton

        binding.ipInput.setOnEditorActionListener { _, _, _ ->
            val ipInput = binding.ipInput.text.toString().trim()

            if (ipInput.isNotEmpty()) {
                val cleanedIp = ipInput.removePrefix("ws://").removePrefix("wss://").split(":")[0]
                val fullUrl = "ws://$cleanedIp:8765"

                val listener = MyWebSocketListener(this)
                webSocketManager = WebSocketManager(fullUrl, listener, this)
                webSocketManager.connect()

                Toast.makeText(this, "Connect with $fullUrl", Toast.LENGTH_SHORT).show()
            } else {
                Toast.makeText(this, "Enter your backend IP", Toast.LENGTH_SHORT).show()
            }
            true
        }

        if (allPermissionsGranted()) {
            startCamera()
        } else {
            ActivityCompat.requestPermissions(this, REQUIRED_PERMISSIONS, REQUEST_CODE_PERMISSIONS)
        }

        cameraExecutor = Executors.newSingleThreadExecutor()

        button.setOnClickListener {
            if (nightMode == "normalmode") {
                button.text = "nightmode: on"
                nightMode = "NIGHT_MODE"
            } else {
                button.text = "nightmode: off"
                nightMode = "normalmode"
            }
        }

        temporarySigns.myList.observe(this, Observer { detectedSigns ->
            val currentTime = System.currentTimeMillis()


            detectedSigns.forEach { sign ->
                signTimestamps[sign] = currentTime


                if (!displayedImages.containsKey(sign)) {
                    val imageResource = resources.getIdentifier(sign, "drawable", packageName)
                    if (imageResource != 0) {
                        val imageView = ImageView(this).apply {
                            setImageResource(imageResource)
                            layoutParams = LinearLayout.LayoutParams(200, 200).apply {
                                marginStart = 8
                                marginEnd = 8
                            }
                        }
                        binding.imageContainerTemporary.addView(imageView)
                        displayedImages[sign] = imageView
                        Log.d(TAG, "Added image: $sign")
                    } else {
                        Log.e(TAG, "No image found for: $sign")
                    }
                }
            }

            val iterator = displayedImages.iterator()
            while (iterator.hasNext()) {
                val (sign, imageView) = iterator.next()
                val lastSeen = signTimestamps[sign] ?: 0
                if (currentTime - lastSeen > signDisplayDuration) {
                    binding.imageContainerTemporary.removeView(imageView)
                    iterator.remove()
                    signTimestamps.remove(sign)
                    Log.d(TAG, "Removed image: $sign after timeout")
                }
            }
        })
    }

    override fun onMessageReceived(message: String) {
        runOnUiThread {
            val jsonArray = JSONArray(message)
            val newBoxList: MutableList<BoundingBox> = mutableListOf()
            val listOfSigns: MutableList<String> = mutableListOf()

            for (i in 0 until jsonArray.length()) {
                val jsonObject = jsonArray.getJSONObject(i)
                val className = turnStringToImageName(jsonObject.getString("class"))
                val bbox = jsonObject.getJSONArray("bbox")
                val confidence = jsonObject.getDouble("confidence")

                if (confidence < 0.7) break

                val x1 = bbox.getDouble(0)
                val y1 = bbox.getDouble(1)
                val x2 = bbox.getDouble(2)
                val y2 = bbox.getDouble(3)

                val newBox = BoundingBox(x1.toFloat(), y1.toFloat(), x2.toFloat(), y2.toFloat(), 0f, 0f, 0f, 0f, 0f, 0, className)
                newBoxList.add(newBox)

                listOfSigns.add(className)
            }

            binding.overlay.apply {
                setResults(newBoxList)
                invalidate()
            }

            temporarySigns.updateList(listOfSigns)
        }
    }

    override fun onError(error: String) {
        runOnUiThread {
            Toast.makeText(this, "error: $error", Toast.LENGTH_SHORT).show()
        }
    }

    fun sendBinaryMessageToWebSocket(header: String, message: ByteArray) {
        webSocketManager.sendBinaryData(header, message)
    }

    fun sendMessageToWebSocket(message: String) {
        webSocketManager.sendMessage(message)
    }

    private fun startCamera() {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(this)
        cameraProviderFuture.addListener({
            cameraProvider = cameraProviderFuture.get()
            bindCameraUseCases()
        }, ContextCompat.getMainExecutor(this))
    }

    private fun bindCameraUseCases() {
        val cameraProvider = cameraProvider ?: throw IllegalStateException("Camera initialization failed.")

        val rotation = binding.viewFinder.display.rotation

        val cameraSelector = CameraSelector.Builder()
            .requireLensFacing(CameraSelector.LENS_FACING_BACK)
            .build()

        preview = Preview.Builder()
            .setTargetAspectRatio(AspectRatio.RATIO_4_3)
            .setTargetRotation(rotation)
            .build()

        imageAnalyzer = ImageAnalysis.Builder()
            .setTargetAspectRatio(AspectRatio.RATIO_4_3)
            .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
            .setTargetRotation(rotation)
            .setOutputImageFormat(ImageAnalysis.OUTPUT_IMAGE_FORMAT_RGBA_8888)
            .build()

        imageAnalyzer?.setAnalyzer(cameraExecutor) { imageProxy ->
            val bitmapBuffer = Bitmap.createBitmap(
                imageProxy.width,
                imageProxy.height,
                Bitmap.Config.ARGB_8888
            )
            imageProxy.use {
                bitmapBuffer.copyPixelsFromBuffer(imageProxy.planes[0].buffer)
            }
            imageProxy.close()

            val matrix = Matrix().apply {
                postRotate(imageProxy.imageInfo.rotationDegrees.toFloat())
                if (isFrontCamera) {
                    postScale(-1f, 1f, imageProxy.width.toFloat(), imageProxy.height.toFloat())
                }
            }

            val rotatedBitmap = Bitmap.createBitmap(
                bitmapBuffer, 0, 0, bitmapBuffer.width, bitmapBuffer.height, matrix, true
            )

            if (::webSocketManager.isInitialized) {
                sendBinaryMessageToWebSocket(nightMode, bitmapToByteArray(rotatedBitmap))
            }
        }

        cameraProvider.unbindAll()

        try {
            camera = cameraProvider.bindToLifecycle(this, cameraSelector, preview, imageAnalyzer)
            preview?.setSurfaceProvider(binding.viewFinder.surfaceProvider)
        } catch (exc: Exception) {
            Log.e(TAG, "Use case binding failed", exc)
        }
    }

    fun bitmapToByteArray(bitmap: Bitmap, format: Bitmap.CompressFormat = Bitmap.CompressFormat.JPEG, quality: Int = 100): ByteArray {
        val outputStream = ByteArrayOutputStream()
        bitmap.compress(format, quality, outputStream)
        return outputStream.toByteArray()
    }

    private fun allPermissionsGranted() = REQUIRED_PERMISSIONS.all {
        ContextCompat.checkSelfPermission(baseContext, it) == PackageManager.PERMISSION_GRANTED
    }

    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()) {
        if (it[Manifest.permission.CAMERA] == true) startCamera()
    }

    override fun onDestroy() {
        super.onDestroy()
        cameraExecutor.shutdown()
    }

    override fun onResume() {
        super.onResume()
        if (allPermissionsGranted()) {
            startCamera()
        } else {
            requestPermissionLauncher.launch(REQUIRED_PERMISSIONS)
        }
    }

    companion object {
        private const val TAG = "Camera"
        private const val REQUEST_CODE_PERMISSIONS = 10
        private val REQUIRED_PERMISSIONS = arrayOf(Manifest.permission.CAMERA)
    }

    private fun turnStringToImageName(str: String): String {
        return str.replace(" ", "_").replace("(", "").replace(")", "")
    }

    override fun onConnected() {
        runOnUiThread {
            Toast.makeText(this, "WebSocket connected!", Toast.LENGTH_SHORT).show()
        }
    }
}
