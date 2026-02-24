package com.example.hybridlink.data

import com.example.hybridlink.model.FileMetadata
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

class TransferStateManager(
    private val fileMetadata: FileMetadata
) {

    private val _transferState = MutableStateFlow<TransferState>(TransferState.Idle)
    val transferState: StateFlow<TransferState> = _transferState

    fun start() {
        _transferState.value = TransferState.InProgress(0f)
    }

    fun pause() {
        _transferState.value = TransferState.Paused
    }

    fun resume() {
        _transferState.value = TransferState.InProgress(0f) // TODO: Get actual progress
    }

    fun complete() {
        _transferState.value = TransferState.Completed
    }

    fun fail(error: Throwable) {
        _transferState.value = TransferState.Failed(error)
    }

    fun updateProgress(progress: Float) {
        _transferState.value = TransferState.InProgress(progress)
    }
}

sealed class TransferState {
    object Idle : TransferState()
    data class InProgress(val progress: Float) : TransferState()
    object Paused : TransferState()
    object Completed : TransferState()
    data class Failed(val error: Throwable) : TransferState()
}
