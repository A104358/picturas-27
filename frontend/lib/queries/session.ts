import { useQuery } from "@tanstack/react-query";
import { parseStoredSession } from "../session-state";

export const useGetSession = () => {
  return useQuery({
    queryKey: ["session"],
    queryFn: () => {
      return parseStoredSession(localStorage.getItem("session"));
    },
    retry: false,
  });
};
