package com.buildrelay.app

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.core.content.FileProvider
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.text.SimpleDateFormat
import java.util.*

class MainActivity : ComponentActivity() {
  private val notificationPermission = registerForActivityResult(ActivityResultContracts.RequestPermission()) {}

  override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
      notificationPermission.launch(Manifest.permission.POST_NOTIFICATIONS)
    }
    setContent { BuildRelayApp() }
  }
}

private enum class Tab { Build, Activity, Settings }

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BuildRelayApp() {
  val context = LocalContext.current
  val scope = rememberCoroutineScope()
  val tokenStore = remember { SecureToken(context) }
  val github = remember { GitHubClient() }
  val prefs = remember { context.getSharedPreferences("buildrelay", 0) }
  var darkMode by remember { mutableStateOf(prefs.getBoolean("dark", false)) }
  var tab by remember { mutableStateOf(Tab.Build) }
  var githubUser by remember { mutableStateOf(prefs.getString("github_user", null)) }
  var token by remember { mutableStateOf(tokenStore.read()) }
  var owner by remember { mutableStateOf(prefs.getString("owner", "") ?: "") }
  var repo by remember { mutableStateOf(prefs.getString("repo", "") ?: "") }
  var branch by remember { mutableStateOf(prefs.getString("branch", "main") ?: "main") }
  var builds by remember { mutableStateOf(loadBuilds(prefs)) }
  var busy by remember { mutableStateOf(false) }
  var message by remember { mutableStateOf<String?>(null) }
  var preflight by remember { mutableStateOf<List<Pair<Boolean, String>>>(emptyList()) }

  fun persistProject() {
    prefs.edit().putString("owner", owner).putString("repo", repo).putString("branch", branch).apply()
  }
  fun persistBuilds() { saveBuilds(prefs, builds) }

  MaterialTheme(colorScheme = if (darkMode) darkColorScheme() else lightColorScheme()) {
    Scaffold(
      topBar = {
        TopAppBar(
          title = {
            Column {
              Text("BuildRelay", fontWeight = FontWeight.Bold)
              Text("APK builds through GitHub Actions", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
          }
        )
      },
      bottomBar = {
        NavigationBar {
          NavigationBarItem(selected = tab == Tab.Build, onClick = { tab = Tab.Build }, icon = { Icon(Icons.Default.Build, null) }, label = { Text("Build") })
          NavigationBarItem(selected = tab == Tab.Activity, onClick = { tab = Tab.Activity }, icon = { Icon(Icons.Default.History, null) }, label = { Text("Activity") })
          NavigationBarItem(selected = tab == Tab.Settings, onClick = { tab = Tab.Settings }, icon = { Icon(Icons.Default.Settings, null) }, label = { Text("Settings") })
        }
      },
      snackbarHost = {
        message?.let { msg ->
          Snackbar(modifier = Modifier.padding(12.dp), action = { TextButton(onClick = { message = null }) { Text("OK") } }) { Text(msg) }
        }
      }
    ) { padding ->
      when (tab) {
        Tab.Build -> BuildScreen(
          modifier = Modifier.padding(padding),
          connectedUser = githubUser,
          owner = owner,
          repo = repo,
          branch = branch,
          preflight = preflight,
          busy = busy,
          onOwner = { owner = it },
          onRepo = { repo = it },
          onBranch = { branch = it },
          onCheck = {
            val t = token
            if (t == null) { message = "Connect GitHub in Settings first"; tab = Tab.Settings }
            else if (owner.isBlank() || repo.isBlank() || branch.isBlank()) message = "Enter owner, repository and branch"
            else scope.launch {
              busy = true
              persistProject()
              runCatching { github.preflight(t, owner.trim(), repo.trim(), branch.trim()) }
                .onSuccess { preflight = it; message = if (it.all { c -> c.first }) "Ready to build" else "Preflight found issues" }
                .onFailure { message = it.message ?: "Preflight failed" }
              busy = false
            }
          },
          onBuild = {
            val t = token
            if (t == null) { message = "Connect GitHub first"; tab = Tab.Settings }
            else if (preflight.isEmpty() || preflight.any { !it.first }) message = "Run checks and fix failed items first"
            else scope.launch {
              busy = true
              persistProject()
              val id = UUID.randomUUID().toString()
              var item = BuildItem(id, owner.trim(), repo.trim(), branch.trim())
              builds = listOf(item) + builds
              persistBuilds()
              tab = Tab.Activity
              runCatching { github.dispatch(t, item.owner, item.repo, item.branch) }
                .onSuccess { notBefore ->
                  var run: GitHubClient.Run? = null
                  repeat(20) {
                    if (run == null) {
                      delay(1500)
                      run = runCatching { github.newestRun(t, item.owner, item.repo, notBefore) }.getOrNull()
                    }
                  }
                  val first = run ?: error("GitHub accepted the build but the workflow run did not appear")
                  item = item.copy(runId = first.id, runNumber = first.number, status = "Building", detail = "GitHub Actions run #${first.number}")
                  builds = builds.map { if (it.id == id) item else it }; persistBuilds()
                  while (true) {
                    val r = github.run(t, item.owner, item.repo, first.id)
                    if (r.status == "completed") {
                      if (r.conclusion == "success") {
                        val artifact = github.artifactId(t, item.owner, item.repo, first.id)
                        item = item.copy(status = "Complete", detail = "APK ready", artifactId = artifact, completedAt = System.currentTimeMillis())
                      } else {
                        item = item.copy(status = if (r.conclusion == "cancelled") "Cancelled" else "Failed", detail = "GitHub Actions: ${r.conclusion ?: "failed"}", error = "Open the GitHub Actions run for full compiler logs", completedAt = System.currentTimeMillis())
                      }
                      builds = builds.map { if (it.id == id) item else it }; persistBuilds(); break
                    }
                    item = item.copy(status = if (r.status == "queued") "Queued" else "Building", detail = if (r.status == "queued") "Waiting for runner" else "Compiling APK")
                    builds = builds.map { if (it.id == id) item else it }; persistBuilds()
                    delay(4000)
                  }
                }
                .onFailure {
                  item = item.copy(status = "Failed", detail = "Build could not start", error = it.message, completedAt = System.currentTimeMillis())
                  builds = builds.map { if (it.id == id) item else it }; persistBuilds(); message = it.message
                }
              busy = false
            }
          }
        )
        Tab.Activity -> ActivityScreen(
          modifier = Modifier.padding(padding),
          builds = builds,
          token = token,
          github = github,
          onUpdate = { updated -> builds = builds.map { if (it.id == updated.id) updated else it }; persistBuilds() },
          onMessage = { message = it }
        )
        Tab.Settings -> SettingsScreen(
          modifier = Modifier.padding(padding),
          githubUser = githubUser,
          darkMode = darkMode,
          busy = busy,
          onDarkMode = { darkMode = it; prefs.edit().putBoolean("dark", it).apply() },
          onConnect = { entered ->
            scope.launch {
              busy = true
              runCatching { github.whoAmI(entered.trim()) }
                .onSuccess { user -> tokenStore.save(entered.trim()); token = entered.trim(); githubUser = user; prefs.edit().putString("github_user", user).apply(); message = "Connected as $user" }
                .onFailure { message = it.message ?: "GitHub connection failed" }
              busy = false
            }
          },
          onDisconnect = { tokenStore.clear(); token = null; githubUser = null; prefs.edit().remove("github_user").apply(); message = "GitHub disconnected" }
        )
      }
    }
  }
}

@Composable
private fun BuildScreen(
  modifier: Modifier,
  connectedUser: String?,
  owner: String,
  repo: String,
  branch: String,
  preflight: List<Pair<Boolean, String>>,
  busy: Boolean,
  onOwner: (String) -> Unit,
  onRepo: (String) -> Unit,
  onBranch: (String) -> Unit,
  onCheck: () -> Unit,
  onBuild: () -> Unit
) {
  LazyColumn(modifier = modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
    item {
      StatusCard(if (connectedUser != null) "GitHub connected" else "GitHub not connected", connectedUser ?: "Connect from Settings before building", connectedUser != null)
    }
    item { Text("Project", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold) }
    item { OutlinedTextField(owner, onOwner, label = { Text("GitHub owner") }, singleLine = true, modifier = Modifier.fillMaxWidth()) }
    item { OutlinedTextField(repo, onRepo, label = { Text("Repository") }, singleLine = true, modifier = Modifier.fillMaxWidth()) }
    item { OutlinedTextField(branch, onBranch, label = { Text("Branch") }, singleLine = true, modifier = Modifier.fillMaxWidth()) }
    if (preflight.isNotEmpty()) {
      item { Text("Checks", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold) }
      items(preflight) { check ->
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
          Icon(if (check.first) Icons.Default.CheckCircle else Icons.Default.Error, null, tint = if (check.first) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.error)
          Text(check.second)
        }
      }
    }
    item {
      Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
        OutlinedButton(onClick = onCheck, enabled = !busy, modifier = Modifier.weight(1f), shape = RoundedCornerShape(8.dp)) { Text("Run checks") }
        Button(onClick = onBuild, enabled = !busy && preflight.isNotEmpty() && preflight.all { it.first }, modifier = Modifier.weight(1f), shape = RoundedCornerShape(8.dp)) {
          if (busy) CircularProgressIndicator(Modifier.size(18.dp), strokeWidth = 2.dp) else Text("Build APK")
        }
      }
    }
    item {
      Text("Like Expo: connect once, select a project, build, then use Activity to download the APK.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
  }
}

@Composable
private fun ActivityScreen(
  modifier: Modifier,
  builds: List<BuildItem>,
  token: String?,
  github: GitHubClient,
  onUpdate: (BuildItem) -> Unit,
  onMessage: (String) -> Unit
) {
  val context = LocalContext.current
  val scope = rememberCoroutineScope()
  if (builds.isEmpty()) {
    Box(modifier.fillMaxSize(), contentAlignment = Alignment.Center) { Text("No builds yet") }
    return
  }
  LazyColumn(modifier = modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
    item { Text("Activity", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold) }
    items(builds, key = { it.id }) { build ->
      ElevatedCard(modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
          Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Column {
              Text(build.repo, fontWeight = FontWeight.SemiBold)
              Text("${build.owner}/${build.repo} · ${build.branch}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            AssistChip(onClick = {}, label = { Text(build.status) })
          }
          Text(build.detail, style = MaterialTheme.typography.bodyMedium)
          build.runNumber?.let { Text("Run #$it", fontFamily = FontFamily.Monospace, style = MaterialTheme.typography.bodySmall) }
          build.error?.let { Text(it, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall) }
          Text(formatTime(build.requestedAt), style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)

          if (build.status == "Complete" && build.artifactId != null) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
              Button(onClick = {
                val t = token
                if (t == null) {
                  onMessage("Connect GitHub first")
                } else {
                  scope.launch {
                    runCatching { github.downloadApk(context, t, build.owner, build.repo, build.artifactId, build.runNumber ?: 0) }
                      .onSuccess { file -> onUpdate(build.copy(apkPath = file.absolutePath, detail = "Downloaded · ${file.length() / 1024 / 1024} MB")); onMessage("APK downloaded") }
                      .onFailure { onMessage(it.message ?: "Download failed") }
                  }
                }
              }, shape = RoundedCornerShape(8.dp)) { Icon(Icons.Default.Download, null); Spacer(Modifier.width(6.dp)); Text(if (build.apkPath == null) "Download" else "Download again") }
              if (build.apkPath != null && File(build.apkPath).exists()) {
                OutlinedButton(onClick = { installApk(context, File(build.apkPath)) }, shape = RoundedCornerShape(8.dp)) { Text("Install") }
                OutlinedButton(onClick = { shareApk(context, File(build.apkPath)) }, shape = RoundedCornerShape(8.dp)) { Text("Share") }
              }
            }
          }
          if ((build.status == "Queued" || build.status == "Building") && build.runId != null && token != null) {
            TextButton(onClick = { scope.launch { runCatching { github.cancel(token, build.owner, build.repo, build.runId) }.onSuccess { onUpdate(build.copy(status = "Cancelled", detail = "Cancellation requested")) }.onFailure { onMessage(it.message ?: "Cancel failed") } } }) { Text("Cancel build") }
          }
        }
      }
    }
  }
}

@Composable
private fun SettingsScreen(
  modifier: Modifier,
  githubUser: String?,
  darkMode: Boolean,
  busy: Boolean,
  onDarkMode: (Boolean) -> Unit,
  onConnect: (String) -> Unit,
  onDisconnect: () -> Unit
) {
  var entered by remember { mutableStateOf("") }
  var show by remember { mutableStateOf(false) }
  LazyColumn(modifier = modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
    item { Text("Settings", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold) }
    item {
      ElevatedCard(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
          Text("GitHub", fontWeight = FontWeight.SemiBold)
          Text(if (githubUser != null) "Connected as $githubUser" else "Connect with a fine-grained token", color = MaterialTheme.colorScheme.onSurfaceVariant)
          if (githubUser == null) {
            OutlinedTextField(
              value = entered,
              onValueChange = { entered = it },
              label = { Text("GitHub token") },
              visualTransformation = if (show) VisualTransformation.None else PasswordVisualTransformation(),
              trailingIcon = { TextButton(onClick = { show = !show }) { Text(if (show) "Hide" else "Show") } },
              singleLine = true,
              modifier = Modifier.fillMaxWidth()
            )
            Button(onClick = { onConnect(entered) }, enabled = entered.isNotBlank() && !busy, shape = RoundedCornerShape(8.dp)) { Text("Connect GitHub") }
            Text("Recommended permissions for selected repositories: Contents read/write and Actions read/write.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
          } else {
            OutlinedButton(onClick = onDisconnect, shape = RoundedCornerShape(8.dp)) { Text("Disconnect") }
          }
        }
      }
    }
    item {
      ElevatedCard(Modifier.fillMaxWidth()) {
        Row(Modifier.padding(14.dp).fillMaxWidth(), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.SpaceBetween) {
          Column(Modifier.weight(1f)) { Text("Dark mode", fontWeight = FontWeight.SemiBold); Text("Use a high-contrast dark interface", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant) }
          Switch(checked = darkMode, onCheckedChange = onDarkMode)
        }
      }
    }
    item {
      ElevatedCard(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
          Text("How builds work", fontWeight = FontWeight.SemiBold)
          Text("BuildRelay installs one GitHub Actions workflow in the selected repository. It runs assembleDebug, uploads the APK for 30 days, and Activity tracks the real workflow status.", style = MaterialTheme.typography.bodySmall)
          Text("No Expo account, EAS project, Supabase backend, or paid BuildRelay server is required.", style = MaterialTheme.typography.bodySmall)
        }
      }
    }
  }
}

@Composable
private fun StatusCard(title: String, subtitle: String, ok: Boolean) {
  ElevatedCard(Modifier.fillMaxWidth()) {
    Row(Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
      Icon(if (ok) Icons.Default.CloudDone else Icons.Default.CloudOff, null, tint = if (ok) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.error)
      Column { Text(title, fontWeight = FontWeight.SemiBold); Text(subtitle, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant) }
    }
  }
}

private fun installApk(context: android.content.Context, file: File) {
  if (Build.VERSION.SDK_INT >= 26 && !context.packageManager.canRequestPackageInstalls()) {
    context.startActivity(Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES, Uri.parse("package:${context.packageName}")))
    return
  }
  val uri = FileProvider.getUriForFile(context, "${context.packageName}.files", file)
  context.startActivity(Intent(Intent.ACTION_VIEW).setDataAndType(uri, "application/vnd.android.package-archive").addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_ACTIVITY_NEW_TASK))
}

private fun shareApk(context: android.content.Context, file: File) {
  val uri = FileProvider.getUriForFile(context, "${context.packageName}.files", file)
  context.startActivity(Intent.createChooser(Intent(Intent.ACTION_SEND).setType("application/vnd.android.package-archive").putExtra(Intent.EXTRA_STREAM, uri).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION), "Share APK"))
}

private fun formatTime(ms: Long): String = SimpleDateFormat("dd MMM yyyy, HH:mm", Locale.getDefault()).format(Date(ms))

private fun loadBuilds(prefs: android.content.SharedPreferences): List<BuildItem> = runCatching {
  val arr = JSONArray(prefs.getString("builds", "[]"))
  buildList {
    for (i in 0 until arr.length()) {
      val o = arr.getJSONObject(i)
      add(BuildItem(
        id = o.getString("id"), owner = o.getString("owner"), repo = o.getString("repo"), branch = o.getString("branch"),
        runId = if (o.has("runId") && !o.isNull("runId")) o.getLong("runId") else null,
        runNumber = if (o.has("runNumber") && !o.isNull("runNumber")) o.getInt("runNumber") else null,
        status = o.optString("status", "Queued"), detail = o.optString("detail", ""),
        artifactId = if (o.has("artifactId") && !o.isNull("artifactId")) o.getLong("artifactId") else null,
        apkPath = o.optString("apkPath").takeIf { it.isNotBlank() }, requestedAt = o.optLong("requestedAt", System.currentTimeMillis()),
        completedAt = if (o.has("completedAt") && !o.isNull("completedAt")) o.getLong("completedAt") else null,
        error = o.optString("error").takeIf { it.isNotBlank() }
      ))
    }
  }
}.getOrDefault(emptyList())

private fun saveBuilds(prefs: android.content.SharedPreferences, builds: List<BuildItem>) {
  val arr = JSONArray()
  builds.take(100).forEach { b ->
    arr.put(JSONObject().apply {
      put("id", b.id); put("owner", b.owner); put("repo", b.repo); put("branch", b.branch)
      put("runId", b.runId ?: JSONObject.NULL); put("runNumber", b.runNumber ?: JSONObject.NULL)
      put("status", b.status); put("detail", b.detail); put("artifactId", b.artifactId ?: JSONObject.NULL)
      put("apkPath", b.apkPath ?: ""); put("requestedAt", b.requestedAt); put("completedAt", b.completedAt ?: JSONObject.NULL); put("error", b.error ?: "")
    })
  }
  prefs.edit().putString("builds", arr.toString()).apply()
}
