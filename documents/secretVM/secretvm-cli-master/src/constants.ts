export const API_ENDPOINTS = {
    AUTH: {
        CSRF: "/api/auth/csrf",
        KEPLR_CALLBACK: "/api/auth/callback/keplr",
        SESSION: "/api/auth/session",
    },
    VM: {
        INSTANCES: "/api/vm/instances",
        CREATE: "/api/vm/create",
        DETAILS: (vmId: string) => `/api/vm/${vmId}`,
        STOP: (vmId: string) => `/api/vm/${vmId}/stop`,
        START: (vmId: string) => `/api/vm/${vmId}/start`,
        TERMINATE: (vmId: string) => `/api/vm/${vmId}/terminate`,
        LOGS: (vmId: string) => `/api/vm/${vmId}/docker_logs`,
        CPU_ATTESTATION: (vmId: string) => `/api/vm/${vmId}/cpu`,
    },
};
