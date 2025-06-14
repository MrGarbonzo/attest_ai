import axios, { AxiosInstance } from "axios";
import { URLSearchParams } from "url";
import { CsrfResponse, KeplrLoginResponse } from "../types";
import { API_ENDPOINTS } from "../constants";

export async function getCsrfToken(client: AxiosInstance): Promise<string> {
    try {
        const response = await client.get<CsrfResponse>(
            API_ENDPOINTS.AUTH.CSRF,
        );
        if (!response.data.csrfToken) {
            throw new Error("CSRF token not found in response.");
        }
        return response.data.csrfToken;
    } catch (error) {
        if (axios.isAxiosError(error)) {
            console.error(
                "Error fetching CSRF token:",
                error.response?.status,
                error.response?.data || error.message,
            );
        } else {
            console.error(
                "An unexpected error occurred while fetching CSRF token:",
                error,
            );
        }
        throw error;
    }
}

export async function loginWithKeplr(
    client: AxiosInstance,
    walletAddress: string,
    signature: string,
    message: string,
    csrfToken: string,
): Promise<KeplrLoginResponse | null> {
    const params = new URLSearchParams();
    params.append("walletAddress", walletAddress);
    params.append("signature", signature);
    params.append("message", message);
    params.append("csrfToken", csrfToken);
    params.append("json", "true");

    try {
        const response = await client.post<KeplrLoginResponse>(
            API_ENDPOINTS.AUTH.KEPLR_CALLBACK,
            params.toString(),
            {
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            },
        );
        return response.data;
    } catch (error) {
        if (axios.isAxiosError(error)) {
            console.error(
                "Keplr login failed:",
                error.response?.status,
                error.response?.data || error.message,
            );
            // If 302 redirect, it might still be a success if cookie was set
            if (
                error.response?.status === 302 &&
                error.response?.headers.location
            ) {
                return { url: error.response.headers.location };
            }
        } else {
            console.error(
                "An unexpected error occurred during Keplr login:",
                error,
            );
        }
        return null;
    }
}
