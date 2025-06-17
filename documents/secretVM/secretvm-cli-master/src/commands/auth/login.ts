import http from "http";
import { URLSearchParams } from "url";
import open from "open";
import { Cookie, CookieJar } from "tough-cookie";
import { saveSession, SERVER_BASE_URL } from "../../services/apiClient";
import { GlobalOptions } from "../../types";
import { successResponse, handleCommandExecution } from "../../utils";

export async function loginCommand(
    globalOptions: GlobalOptions,
): Promise<void> {
    await handleCommandExecution(
        globalOptions,
        async (): Promise<void> => {
            if (!globalOptions.interactive) {
                throw new Error(
                    "Browser login requires interactive mode. Please use the -i flag.",
                );
            }
            await new Promise<void>((resolve, reject) => {
                let server: http.Server;
                let timeoutId: NodeJS.Timeout;

                const cleanup = (error?: Error) => {
                    clearTimeout(timeoutId); // Always clear the timeout
                    server.close(() => {
                        // Close the server
                        console.debug("Local callback server closed.");
                        if (error) {
                            reject(error);
                        } else {
                            resolve();
                        }
                    });
                };
                server = http.createServer(async (req, res) => {
                    try {
                        if (!req.url) {
                            throw new Error("Request URL is missing.");
                        }

                        const url = new URL(
                            req.url,
                            `http://${req.headers.host}`,
                        );
                        if (url.pathname === "/callback") {
                            const params = url.searchParams;
                            const sessionToken = params.get("sessionToken");
                            const tokenName = params.get("tokenName");

                            if (!sessionToken || !tokenName) {
                                throw new Error(
                                    "Session token or token name missing in callback.",
                                );
                            }

                            console.info(
                                "Session token received from browser.",
                            );

                            // --- Reconstruct the session cookie and save it ---
                            const jar = new CookieJar();
                            const cookie = new Cookie({
                                key: tokenName,
                                value: sessionToken,
                                domain: new URL(SERVER_BASE_URL).hostname, // Get domain from your server URL
                                path: "/",
                                httpOnly: true,
                                secure: SERVER_BASE_URL.startsWith("https"),
                            });

                            await jar.setCookie(cookie, SERVER_BASE_URL);
                            await saveSession(jar);

                            res.writeHead(200, { "Content-Type": "text/html" });
                            res.end(
                                "<h1>Success!</h1><p>You are logged in. You can now close this browser tab and return to your terminal.</p>",
                            );

                            cleanup();
                        } else {
                            res.writeHead(404);
                            res.end("Not Found");
                        }
                    } catch (error) {
                        console.error("Error in local callback server:", error);
                        res.writeHead(500, { "Content-Type": "text/html" });
                        res.end(
                            "<h1>Error</h1><p>An error occurred. Please check the CLI for details.</p>",
                        );
                        cleanup(error as Error);
                    }
                });

                // Start listening on a random available port
                server.listen(0, () => {
                    const port = (server.address() as import("net").AddressInfo)
                        .port;
                    console.info(
                        `Local server listening on http://localhost:${port}`,
                    );

                    const loginUrlParams = new URLSearchParams({
                        cliCallbackPort: String(port),
                    });

                    const loginUrl = `${SERVER_BASE_URL}/sign-in?${loginUrlParams.toString()}`;

                    console.info("Opening your browser to complete login...");
                    console.debug(`Login URL: ${loginUrl}`);

                    open(loginUrl);
                });

                server.on("error", (err) => {
                    cleanup(err);
                });

                // Timeout for the login process
                timeoutId = setTimeout(() => {
                    cleanup(
                        new Error(
                            "Login timed out. The local server did not receive a callback within 2 minutes.",
                        ),
                    );
                }, 120000); // 2 minutes
            });
        },
        (data: void) => {
            if (!globalOptions.interactive) successResponse(data);
            else console.log("Login successful! Your session has been saved.");
        },
    );
}
