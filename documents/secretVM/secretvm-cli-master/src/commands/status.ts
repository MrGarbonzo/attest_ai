import { getApiClient } from "../services/apiClient";
import { AuthSession, GlobalOptions } from "../types";
import { handleCommandExecution, successResponse } from "../utils";
import { API_ENDPOINTS } from "../constants";
import { AxiosResponse } from "axios";

export async function statusCommand(
    globalOptions: GlobalOptions,
): Promise<void> {
    await handleCommandExecution(
        globalOptions,
        async (): Promise<AxiosResponse> => {
            const apiClient = await getApiClient();
            const response = await apiClient.get<AuthSession>(
                API_ENDPOINTS.AUTH.SESSION,
            );
            if (Object.keys(response.data).length == 0)
                throw new Error("You are not logged in.");
            if (
                !response.data ||
                !response.data.user ||
                !response.data.user.sub
            )
                throw new Error(
                    "Session status unknown or you are not logged in",
                );
            return response;
        },
        (data: AxiosResponse) => {
            if (globalOptions.interactive) {
                console.log(
                    "You are logged in as:",
                    data.data.user.email || data.data.user.sub,
                );
                console.log("Session expires:", data.data.expires || "N/A");
            } else {
                successResponse(data.data);
            }
        },
    );
}
