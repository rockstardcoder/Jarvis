export async function callJarvis(command, payload = {}) {
  try {
    const api = await waitForPywebviewApi();

    if (!api) {
      return {
        ok: false,
        message:
          "Python backend bridge is not connected. Run Jarvis through src\\ui_app.py, not browser/Vite.",
        data: {
          reply:
            "Python backend bridge is not connected. Run Jarvis through src\\ui_app.py, not browser/Vite.",
          meta: "BRIDGE / NOT CONNECTED",
        },
      };
    }

    return await api.handle_command(command, payload);
  } catch (error) {
    return {
      ok: false,
      message: `Frontend bridge error: ${error}`,
      data: {
        reply: `Frontend bridge error: ${error}`,
        meta: "BRIDGE / FRONTEND ERROR",
        error: String(error),
      },
    };
  }
}

function waitForPywebviewApi(timeoutMs = 5000) {
  return new Promise((resolve) => {
    if (window.pywebview?.api?.handle_command) {
      resolve(window.pywebview.api);
      return;
    }

    let resolved = false;

    const finish = () => {
      if (resolved) return;
      resolved = true;

      if (window.pywebview?.api?.handle_command) {
        resolve(window.pywebview.api);
      } else {
        resolve(null);
      }
    };

    window.addEventListener("pywebviewready", finish, { once: true });
    setTimeout(finish, timeoutMs);
  });
}