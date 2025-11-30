import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

const firebaseConfig = {
  apiKey: "AIzaSyBTMOOZHr-ywMJuEtZriUb_rvK9gSCMRyU",
  authDomain: "clankk-e61f8.firebaseapp.com",
  databaseURL: "https://clankk-e61f8-default-rtdb.firebaseio.com",
  projectId: "clankk-e61f8",
  storageBucket: "clankk-e61f8.firebasestorage.app",
  messagingSenderId: "882709669408",
  appId: "1:882709669408:web:f1fba6f5f1d7e9971bbe45",
  measurementId: "G-4YTNMF65Y9"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);
export default app;