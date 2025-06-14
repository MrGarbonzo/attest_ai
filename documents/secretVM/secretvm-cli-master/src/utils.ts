import axios from "axios";
import { GlobalOptions } from "./types";

export function errorResponse(error: any) {
    let logMessage: any;
    if (typeof error === "string") {
        logMessage = error;
    } else if (error instanceof Error) {
        logMessage = error.message;
        if (axios.isAxiosError(error) && error.response) {
            logMessage = {
                message: error.message,
                status: error.response.status,
                data: error.response.data,
            };
        }
    } else {
        logMessage = "An unknown error occurred";
    }
    console.log(JSON.stringify({ status: "error", log: logMessage }));
}

export function successResponse(payload: any) {
    console.log(JSON.stringify({ status: "success", result: payload }));
}

export async function handleCommandExecution<T>(
    globalOptions: GlobalOptions,
    commandLogic: () => Promise<T>,
    successHandler: (data: T) => void,
    customErrorMessages?: { [status: number]: string },
) {
    try {
        const result = await commandLogic();
        successHandler(result);
    } catch (error: any) {
        if (globalOptions.interactive) {
            if (axios.isAxiosError(error)) {
                if (
                    customErrorMessages &&
                    error.response?.status &&
                    customErrorMessages[error.response.status]
                ) {
                    console.error(
                        `Error: ${customErrorMessages[error.response.status]}`,
                    );
                } else if (error.response?.status === 401) {
                    console.error(
                        'Error: Unauthorized. Please login first using the "login" command.',
                    );
                } else if (error.response?.status === 404) {
                    console.error(
                        `Error: Resource not found or you are not authorized.`,
                    );
                } else {
                    const errorMsg =
                        error.response?.data?.message ||
                        error.response?.data ||
                        error.message;
                    console.error(
                        `Error (HTTP ${error.response?.status}): ${errorMsg}`,
                    );
                }
            } else {
                console.error(
                    "An unexpected error occurred:",
                    error.message || error,
                );
            }
        } else {
            errorResponse(error);
        }
    }
}
