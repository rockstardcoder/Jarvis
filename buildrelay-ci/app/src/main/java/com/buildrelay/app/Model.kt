package com.buildrelay.app

data class BuildItem(
  val id: String,
  val owner: String,
  val repo: String,
  val branch: String,
  val runId: Long? = null,
  val runNumber: Int? = null,
  val status: String = "Queued",
  val detail: String = "Waiting for GitHub",
  val artifactId: Long? = null,
  val apkPath: String? = null,
  val requestedAt: Long = System.currentTimeMillis(),
  val completedAt: Long? = null,
  val error: String? = null
)
