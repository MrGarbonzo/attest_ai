import { clearSession } from "../../services/apiClient";
import { successResponse, handleCommandExecution } from "../../utils";
import { GlobalOptions } from "../../types";

export async function logoutCommand(
    globalOptions: GlobalOptions,
): Promise<void> {
    await handleCommandExecution(
        globalOptions,
        async (): Promise<void> => {
            await clearSession();
        },
        (data: void) => {
            if (!globalOptions.interactive) successResponse(data);
            else console.log("Session cleared");
        },
    );
}
