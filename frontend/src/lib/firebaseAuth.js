import { initializeApp } from "firebase/app";
import {
  getAuth,
  GoogleAuthProvider,
  getRedirectResult,
  signInWithRedirect,
} from "firebase/auth";

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

function assertFirebaseConfig() {
  const missing = Object.entries(firebaseConfig)
    .filter(([, value]) => !value)
    .map(([key]) => key);

  if (missing.length > 0) {
    throw new Error(
      `Missing Firebase frontend config: ${missing.join(", ")}. Check frontend/.env VITE_FIREBASE_* values.`
    );
  }
}

assertFirebaseConfig();

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

function makeGoogleProvider() {
  const provider = new GoogleAuthProvider();

  provider.setCustomParameters({
    prompt: "select_account",
  });

  return provider;
}

async function sendResultToJarvis(credential) {
  const idToken = await credential.user.getIdToken();

  const payload = {
    idToken,
    provider: "google",
    email: credential.user.email || "",
    name: credential.user.displayName || "",
    photoURL: credential.user.photoURL || "",
  };

  const response = await fetch("/jarvis-auth/complete", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Jarvis desktop app did not accept the Google login result.");
  }

  window.location.replace("/jarvis-auth/success");
}

export async function startOrFinishGoogleForJarvisBrowser() {
  const credential = await getRedirectResult(auth);

  if (credential?.user) {
    await sendResultToJarvis(credential);
    return;
  }

  await signInWithRedirect(auth, makeGoogleProvider());
}
