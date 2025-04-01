package com.adrian.tsr_app

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Rect
import android.graphics.RectF
import android.util.AttributeSet
import android.view.View
import androidx.core.content.ContextCompat
import java.util.LinkedList
import kotlin.math.max

class OverlayView(context: Context?, attrs: AttributeSet?) : View(context, attrs) {

    private var results = listOf<BoundingBox>()
    private var boxPaint = Paint()
    private var textBackgroundPaint = Paint()
    private var textPaint = Paint()
    private var imageWidth = 480
    private var imageHeight = 640

    private var bounds = Rect()

    init {
        initPaints()
    }

    fun clear() {
        textPaint.reset()
        textBackgroundPaint.reset()
        boxPaint.reset()
        invalidate()
        initPaints()
    }

    private fun initPaints() {
        textBackgroundPaint.color = Color.BLACK
        textBackgroundPaint.style = Paint.Style.FILL
        textBackgroundPaint.textSize = 50f

        textPaint.color = Color.WHITE
        textPaint.style = Paint.Style.FILL
        textPaint.textSize = 50f

        boxPaint.color = ContextCompat.getColor(context!!, R.color.bounding_box_color)
        boxPaint.strokeWidth = 8F
        boxPaint.style = Paint.Style.STROKE
    }

    override fun draw(canvas: Canvas) {
        super.draw(canvas)


        results.forEach {
            val x1Normalized = it.x1 / imageWidth
            val y1Normalized = it.y1 / imageHeight
            val x2Normalized = it.x2 / imageWidth
            val y2Normalized = it.y2 / imageHeight

            val scaledX1 = x1Normalized * width
            val scaledY1 = y1Normalized * height
            val scaledX2 = x2Normalized * width
            val scaledY2 = y2Normalized * height



            canvas.drawRect(scaledX1, scaledY1, scaledX2, scaledY2, boxPaint)
            val drawableText = it.clsName
            println("width" + width + "height: " + height)
            textBackgroundPaint.getTextBounds(drawableText, 0, drawableText.length, bounds)
            val textWidth = bounds.width()
            val textHeight = bounds.height()
            canvas.drawRect(
                scaledX1,
                scaledY1,
                scaledX1 + textWidth + BOUNDING_RECT_TEXT_PADDING,
                scaledY1 + textHeight + BOUNDING_RECT_TEXT_PADDING,
                textBackgroundPaint
            )
            canvas.drawText(drawableText, scaledX1, scaledY1 + bounds.height(), textPaint)

        }
    }

    fun setResults(boundingBoxes: List<BoundingBox>) {
        results = boundingBoxes
        invalidate()
    }

    companion object {
        private const val BOUNDING_RECT_TEXT_PADDING = 8
    }
}