import { getApiClient } from "../../services/apiClient";
import { GlobalOptions } from "../../types";
import { AxiosResponse } from "axios";
import { handleCommandExecution, successResponse } from "../../utils";
import { API_ENDPOINTS } from "../../constants";

export async function vmAttestationCommand(
    vmId: string,
    globalOptions: GlobalOptions,
): Promise<void> {
    if (!vmId || vmId.trim() === "") {
        throw new Error("VM ID is required.");
    }
    const trimmedVmId = vmId.trim();
    await handleCommandExecution(
        globalOptions,
        async (): Promise<AxiosResponse> => {
            const apiClient = await getApiClient();
            return await apiClient.get<string>(
                API_ENDPOINTS.VM.CPU_ATTESTATION(trimmedVmId),
            );
        },
        (data: AxiosResponse) => {
            if (globalOptions.interactive) {
                console.log(data.data);
            } else {
                successResponse(data.data);
            }
        },
    );
}
