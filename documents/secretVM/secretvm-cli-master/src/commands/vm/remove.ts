import inquirer from "inquirer";
import { getApiClient } from "../../services/apiClient";
import { RemoveVmApiResponse, GlobalOptions } from "../../types";
import { API_ENDPOINTS } from "../../constants";
import { AxiosResponse } from "axios";
import { handleCommandExecution, successResponse } from "../../utils";

export async function removeVmCommand(
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
            if (globalOptions.interactive) {
                const confirmation = await inquirer.prompt([
                    {
                        type: "confirm",
                        name: "confirmRemove",
                        message: `🛑 Are you sure you want to remove VM ID "${trimmedVmId}"? This action will terminate the VM and delete its record. This cannot be undone.`,
                        default: false,
                    },
                ]);

                if (!confirmation.confirmRemove) {
                    console.log("VM removal cancelled by user.");
                    throw new Error("Cancelled");
                }
            }

            const apiClient = await getApiClient();
            return await apiClient.delete<RemoveVmApiResponse>(
                API_ENDPOINTS.VM.TERMINATE(trimmedVmId),
            );
        },
        (data: AxiosResponse) => {
            if (globalOptions.interactive) {
                if (data.data) {
                    console.log("\nVM remove request processed successfully!");
                    console.log("------------------------------------------");
                    console.log(
                        `Response Status: ${data.data.status || "N/A"}`,
                    );
                    if (data.data.message) {
                        console.log(`Message: ${data.data.message}`);
                    }
                    console.log("------------------------------------------");
                    console.log(`VM ID "${trimmedVmId}" has been removed.`);
                } else {
                    console.log(
                        "VM remove request processed, but the response was empty or in an unexpected format.",
                    );
                }
            } else {
                successResponse(data.data);
            }
        },
    );
}
