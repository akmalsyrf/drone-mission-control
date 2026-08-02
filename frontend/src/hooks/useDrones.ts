import { useQuery } from "@tanstack/react-query";

import { droneApi } from "@/lib/api";

export function useDrones() {
  return useQuery({
    queryKey: ["drones"],
    queryFn: droneApi.list,
    refetchInterval: 10_000,
  });
}
