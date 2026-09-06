package com.buildrelay.app

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.net.URLEncoder
import java.time.Instant
import java.util.concurrent.TimeUnit
import java.util.zip.ZipFile

class GitHubClient {
  private val client = OkHttpClient.Builder()
    .connectTimeout(30, TimeUnit.SECONDS)
    .readTimeout(120, TimeUnit.SECONDS)
    .writeTimeout(120, TimeUnit.SECONDS)
    .followRedirects(true)
    .build()
  private val json = "application/vnd.github+json".toMediaType()

  private fun request(url: String, token: String) = Request.Builder()
    .url(url)
    .header("Authorization", "Bearer $token")
    .header("Accept", "application/vnd.github+json")
    .header("X-GitHub-Api-Version", "2022-11-28")
    .header("User-Agent", "BuildRelay")

  private fun requireOk(code: Int, body: String, allowed: Set<Int> = setOf(200)): String {
    if (code !in allowed) {
      val msg = runCatching { JSONObject(body).optString("message") }.getOrNull().orEmpty()
      error(if (msg.isBlank()) "GitHub API error $code" else msg)
    }
    return body
  }

  suspend fun whoAmI(token: String): String = withContext(Dispatchers.IO) {
    client.newCall(request("https://api.github.com/user", token).get().build()).execute().use { r ->
      val body = r.body?.string().orEmpty(); requireOk(r.code, body); JSONObject(body).getString("login")
    }
  }

  data class RepoInfo(val defaultBranch: String)
  suspend fun repoInfo(token: String, owner: String, repo: String): RepoInfo = withContext(Dispatchers.IO) {
    client.newCall(request("https://api.github.com/repos/$owner/$repo", token).get().build()).execute().use { r ->
      val body = r.body?.string().orEmpty(); requireOk(r.code, body); RepoInfo(JSONObject(body).getString("default_branch"))
    }
  }

  suspend fun branchExists(token: String, owner: String, repo: String, branch: String): Boolean = withContext(Dispatchers.IO) {
    val b = URLEncoder.encode(branch, "UTF-8")
    client.newCall(request("https://api.github.com/repos/$owner/$repo/branches/$b", token).get().build()).execute().use { it.code == 200 }
  }

  suspend fun fileExists(token: String, owner: String, repo: String, path: String, ref: String): Boolean = withContext(Dispatchers.IO) {
    val encodedPath = path.split('/').joinToString("/") { URLEncoder.encode(it, "UTF-8") }
    val encodedRef = URLEncoder.encode(ref, "UTF-8")
    client.newCall(request("https://api.github.com/repos/$owner/$repo/contents/$encodedPath?ref=$encodedRef", token).get().build()).execute().use { it.code == 200 }
  }

  suspend fun installWorkflow(token: String, owner: String, repo: String, defaultBranch: String) = withContext(Dispatchers.IO) {
    val path = ".github/workflows/buildrelay-android.yml"
    val url = "https://api.github.com/repos/$owner/$repo/contents/$path"
    var sha: String? = null
    client.newCall(request("$url?ref=${URLEncoder.encode(defaultBranch, "UTF-8")}", token).get().build()).execute().use { r ->
      if (r.code == 200) sha = JSONObject(r.body?.string().orEmpty()).optString("sha").takeIf { it.isNotBlank() }
    }
    val encoded = android.util.Base64.encodeToString(WORKFLOW.toByteArray(), android.util.Base64.NO_WRAP)
    val payload = JSONObject().put("message", "Configure BuildRelay APK workflow").put("content", encoded).put("branch", defaultBranch)
    sha?.let { payload.put("sha", it) }
    client.newCall(request(url, token).put(payload.toString().toRequestBody(json)).build()).execute().use { r ->
      val body = r.body?.string().orEmpty(); requireOk(r.code, body, setOf(200, 201))
    }
  }

  suspend fun preflight(token: String, owner: String, repo: String, branch: String): List<Pair<Boolean, String>> {
    val info = repoInfo(token, owner, repo)
    val branchOk = branchExists(token, owner, repo, branch)
    val gradlew = fileExists(token, owner, repo, "gradlew", branch)
    val wrapper = fileExists(token, owner, repo, "gradle/wrapper/gradle-wrapper.properties", branch)
    val settings = fileExists(token, owner, repo, "settings.gradle.kts", branch) || fileExists(token, owner, repo, "settings.gradle", branch)
    if (branchOk && gradlew && wrapper && settings) installWorkflow(token, owner, repo, info.defaultBranch)
    return listOf(
      true to "Repository access",
      branchOk to "Branch '$branch' exists",
      (gradlew && wrapper) to "Gradle wrapper detected",
      settings to "Android Gradle project detected",
      (branchOk && gradlew && wrapper && settings) to "Build workflow ready"
    )
  }

  suspend fun dispatch(token: String, owner: String, repo: String, branch: String): Long = withContext(Dispatchers.IO) {
    val info = repoInfo(token, owner, repo)
    val now = System.currentTimeMillis()
    val url = "https://api.github.com/repos/$owner/$repo/actions/workflows/buildrelay-android.yml/dispatches"
    val payload = JSONObject().put("ref", info.defaultBranch).put("inputs", JSONObject().put("target_ref", branch))
    client.newCall(request(url, token).post(payload.toString().toRequestBody(json)).build()).execute().use { r ->
      val body = r.body?.string().orEmpty(); requireOk(r.code, body, setOf(204))
    }
    now
  }

  data class Run(val id: Long, val number: Int, val status: String, val conclusion: String?, val createdAt: Long)
  suspend fun newestRun(token: String, owner: String, repo: String, notBefore: Long): Run? = withContext(Dispatchers.IO) {
    val url = "https://api.github.com/repos/$owner/$repo/actions/workflows/buildrelay-android.yml/runs?event=workflow_dispatch&per_page=10"
    client.newCall(request(url, token).get().build()).execute().use { r ->
      val body = r.body?.string().orEmpty(); requireOk(r.code, body)
      val arr = JSONObject(body).getJSONArray("workflow_runs")
      for (i in 0 until arr.length()) {
        val o = arr.getJSONObject(i)
        val created = Instant.parse(o.getString("created_at")).toEpochMilli()
        if (created + 10_000 >= notBefore) return@withContext Run(o.getLong("id"), o.getInt("run_number"), o.optString("status"), o.optString("conclusion").takeIf { it.isNotBlank() && it != "null" }, created)
      }
      null
    }
  }

  suspend fun run(token: String, owner: String, repo: String, id: Long): Run = withContext(Dispatchers.IO) {
    client.newCall(request("https://api.github.com/repos/$owner/$repo/actions/runs/$id", token).get().build()).execute().use { r ->
      val body = r.body?.string().orEmpty(); requireOk(r.code, body); val o = JSONObject(body)
      Run(o.getLong("id"), o.getInt("run_number"), o.optString("status"), o.optString("conclusion").takeIf { it.isNotBlank() && it != "null" }, Instant.parse(o.getString("created_at")).toEpochMilli())
    }
  }

  suspend fun cancel(token: String, owner: String, repo: String, id: Long) = withContext(Dispatchers.IO) {
    client.newCall(request("https://api.github.com/repos/$owner/$repo/actions/runs/$id/cancel", token).post(ByteArray(0).toRequestBody(null)).build()).execute().use { r ->
      requireOk(r.code, r.body?.string().orEmpty(), setOf(202, 409))
    }
  }

  suspend fun artifactId(token: String, owner: String, repo: String, runId: Long): Long = withContext(Dispatchers.IO) {
    client.newCall(request("https://api.github.com/repos/$owner/$repo/actions/runs/$runId/artifacts", token).get().build()).execute().use { r ->
      val body = r.body?.string().orEmpty(); requireOk(r.code, body)
      val arr = JSONObject(body).getJSONArray("artifacts")
      for (i in 0 until arr.length()) {
        val o = arr.getJSONObject(i); if (o.optString("name") == "buildrelay-apk") return@withContext o.getLong("id")
      }
      error("APK artifact not found")
    }
  }

  suspend fun downloadApk(context: Context, token: String, owner: String, repo: String, artifactId: Long, runNumber: Int): File = withContext(Dispatchers.IO) {
    val dir = context.getExternalFilesDir(android.os.Environment.DIRECTORY_DOWNLOADS) ?: context.filesDir
    val zip = File(dir, "buildrelay-$runNumber.zip")
    val apk = File(dir, "${repo.replace(' ', '-')}-build-$runNumber.apk")
    val url = "https://api.github.com/repos/$owner/$repo/actions/artifacts/$artifactId/zip"
    client.newCall(request(url, token).get().build()).execute().use { r ->
      if (!r.isSuccessful) error("Artifact download failed: HTTP ${r.code}")
      FileOutputStream(zip).use { out -> r.body?.byteStream()?.copyTo(out) ?: error("Empty artifact") }
    }
    var expected: String? = null
    ZipFile(zip).use { z ->
      z.getEntry("metadata.json")?.let { expected = JSONObject(z.getInputStream(it).bufferedReader().readText()).optString("sha256").takeIf(String::isNotBlank) }
      val entry = z.entries().asSequence().firstOrNull { !it.isDirectory && it.name.endsWith(".apk", true) } ?: error("Artifact contains no APK")
      z.getInputStream(entry).use { input -> apk.outputStream().use { input.copyTo(it) } }
    }
    zip.delete()
    val actual = sha256(apk)
    if (expected != null && !expected.equals(actual, true)) { apk.delete(); error("APK checksum verification failed") }
    apk
  }

  private fun sha256(file: File): String {
    val md = java.security.MessageDigest.getInstance("SHA-256")
    file.inputStream().use { input -> val buf = ByteArray(64 * 1024); while (true) { val n = input.read(buf); if (n <= 0) break; md.update(buf, 0, n) } }
    return md.digest().joinToString("") { "%02x".format(it) }
  }

  companion object {
    val WORKFLOW = """
name: BuildRelay Android APK
on:
  workflow_dispatch:
    inputs:
      target_ref:
        description: Branch or tag to build
        required: true
        default: main
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    env:
      TARGET_REF: ${'$'}{{ inputs.target_ref }}
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${'$'}{{ env.TARGET_REF }}
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '17'
      - name: Validate project
        run: |
          test -f gradlew || { echo "Missing gradlew"; exit 21; }
          test -f gradle/wrapper/gradle-wrapper.properties || { echo "Missing Gradle wrapper"; exit 22; }
          chmod +x gradlew
      - name: Build APK
        run: ./gradlew assembleDebug --stacktrace --no-daemon
      - name: Collect APK
        run: |
          set -e
          APK="$(find . -type f -path '*/build/outputs/apk/*/*.apk' ! -name '*androidTest*' | head -n 1)"
          test -n "$APK" || { echo "No APK generated"; exit 31; }
          mkdir -p buildrelay-output
          cp "$APK" buildrelay-output/app.apk
          SHA="$(sha256sum buildrelay-output/app.apk | awk '{print $1}')"
          SIZE="$(stat -c%s buildrelay-output/app.apk)"
          printf '{"apkFilename":"app.apk","apkSizeBytes":%s,"sha256":"%s"}\n' "$SIZE" "$SHA" > buildrelay-output/metadata.json
      - uses: actions/upload-artifact@v4
        with:
          name: buildrelay-apk
          path: buildrelay-output/
          if-no-files-found: error
          retention-days: 30
""".trimIndent()
  }
}
