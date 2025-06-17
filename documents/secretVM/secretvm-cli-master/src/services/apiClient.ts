import axios, { AxiosInstance } from "axios";
import { CookieJar } from "tough-cookie";
import { wrapper } from "axios-cookiejar-support";
import fs from "fs/promises";
import path from "path";
import os from "os";

export const SERVER_BASE_URL =
    process.env.SERVER_BASE_URL || "https://secretai.scrtlabs.com";

const SESSION_DIR = path.join(os.homedir(), ".secretvm-cli");
const SESSION_FILE = path.join(SESSION_DIR, "session.json");

let currentJar: CookieJar | null = null;

async function ensureSessionDirExists(): Promise<void> {
    try {
        await fs.mkdir(SESSION_DIR, { recursive: true });
        if (process.platform !== "win32") {
            await fs.chmod(SESSION_DIR, 0o700);
        }
    } catch (err) {
        console.warn(
            `Warning: Could not create or set permissions for session directory ${SESSION_DIR}:`,
            err,
        );
    }
}

export async function saveSession(jar: CookieJar): Promise<void> {
    await ensureSessionDirExists();
    try {
        const serializableJar = jar.serializeSync();
        await fs.writeFile(
            SESSION_FILE,
            JSON.stringify(serializableJar, null, 2),
            "utf-8",
        );
        if (process.platform !== "win32") {
            await fs.chmod(SESSION_FILE, 0o600);
        }
        currentJar = jar; // Update current jar in memory
    } catch (error) {
        console.error("Error saving session:", error);
    }
}

export async function loadSession(): Promise<CookieJar | null> {
    if (currentJar) return currentJar; // Return cached jar if already loaded

    try {
        await fs.access(SESSION_FILE); // Check if file exists
        const fileContent = await fs.readFile(SESSION_FILE, "utf-8");
        const serializedJar = JSON.parse(fileContent);
        currentJar = CookieJar.deserializeSync(serializedJar);
        return currentJar;
    } catch (error: any) {
        // It's normal if the file doesn't exist on first run or after logout
        if (error.code !== "ENOENT") {
            console.warn(
                "Warning: Could not load session file:",
                error.message,
            );
        }
        return null;
    }
}

export async function clearSession(): Promise<void> {
    try {
        await fs.unlink(SESSION_FILE);
        currentJar = null; // Clear in-memory jar
    } catch (error: any) {
        if (error.code !== "ENOENT") {
            console.error("Error clearing session:", error);
        }
    }
}

export async function getApiClient(): Promise<AxiosInstance> {
    const jarToUse = (await loadSession()) || new CookieJar();
    return wrapper(
        axios.create({
            jar: jarToUse,
            baseURL: SERVER_BASE_URL,
            withCredentials: true,
        }),
    );
}

export function getCurrentJar(apiClient: AxiosInstance): CookieJar | undefined {
    const anyClient = apiClient as any;
    if (anyClient.defaults && anyClient.defaults.jar) {
        return anyClient.defaults.jar;
    }
    return currentJar || undefined;
}
