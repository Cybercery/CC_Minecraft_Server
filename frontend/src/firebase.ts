import { initializeApp } from "firebase/app";
import { 
  getAuth, 
  GoogleAuthProvider, 
  signInWithPopup, 
  signInWithEmailAndPassword, 
  createUserWithEmailAndPassword, 
  signOut, 
  onAuthStateChanged,
  type User
} from "firebase/auth";

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyApixfl9XC7zmPEbpRArtvoxie-3ZLiUr0",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "minecraft-server-c3ba3.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "minecraft-server-c3ba3",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "minecraft-server-c3ba3.firebasestorage.app",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "738109971914",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:738109971914:web:b464fa1d845a64ba0c0333",
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID || "G-098BHNZZ9S"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();

export {
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged
};
export type { User };
