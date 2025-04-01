package com.adrian.tsr_app

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel

class TemporarySigns: ViewModel() {
    val temporarySigns = setOf(
        "priority at next intersection",
        "priority road",
        "give way",
        "stop",
        "no traffic both ways",
        "no trucks",
        "no entry",
        "danger",
        "bend left",
        "bend right",
        "bend",
        "uneven road",
        "slippery road",
        "road narrows",
        "construction",
        "traffic signal",
        "pedestrian crossing",
        "school crossing",
        "cycles crossing",
        "snow",
        "animals",
        "go right",
        "go left",
        "go straight",
        "go right or straight",
        "go left or straight",
        "keep right",
        "keep left",
        "roundabout"
    )

    private val _myList = MutableLiveData<MutableList<String>>(mutableListOf())
    val myList: LiveData<MutableList<String>> get() = _myList

    fun updateList(newList: List<String>) {
        _myList.value = newList.toMutableList()
    }
}