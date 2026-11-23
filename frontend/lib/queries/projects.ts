import { useQuery } from "@tanstack/react-query";
import {
  fetchProjects,
  fetchProject,
  getProjectImages,
  ProjectImage,
  fetchProjectResults,
} from "../projects";
import { useEffect } from "react";
import { createProjectSocket, retainProjectSocket } from "../project-socket";
import { listProjectShareLinks, fetchSharedProject } from "../projects";
import type { ShareLink } from "../projects";
import { resolveShareLink } from "../projects";

export const useProjectShareLinks = (
  userId: string,
  projectId: string,
  token: string,
) => {
  return useQuery<ShareLink[]>({
    queryKey: ["projectShareLinks", userId, projectId, token],
    queryFn: () => listProjectShareLinks(userId, projectId, token),
    enabled: !!userId && !!projectId && !!token,
  });
};

export const useGetProjects = (uid: string, token: string) => {
  return useQuery({
    queryKey: ["projects", uid, token],
    queryFn: () => fetchProjects(uid, token),
    enabled: !!uid && !!token, // só faz request se tiver uid+token
  });
};


export const useGetProject = (
  uid: string,
  pid: string,
  token: string,
  ownerId?: string,
  shareId?: string,
) => {
  return useQuery({
    queryKey: ["project", uid, pid, token, ownerId, shareId],
    queryFn: () => fetchProject(uid, pid, token, ownerId, shareId),
  });
};

export const useGetProjectImages = (
  uid: string,
  pid: string,
  token: string,
  initialData?: ProjectImage[],
) => {
  return useQuery({
    queryKey: ["projectImages", uid, pid, token],
    queryFn: () => getProjectImages(uid, pid, token),
    initialData: initialData,
  });
};

export const useGetSocket = (token: string) => {
  const query = useQuery({
    queryKey: ["socket", token],
    queryFn: () => createProjectSocket(token),
    enabled: !!token,
    staleTime: Infinity,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
  });
  useEffect(() => {
    if (query.data) return retainProjectSocket(query.data);
  }, [query.data]);
  return query;
};

export const useGetProjectResults = (
  uid: string,
  pid: string,
  token: string,
  ownerId?: string,
  shareId?: string,
) => {
  return useQuery({
    queryKey: ["projectResults", uid, pid, token, ownerId, shareId],
    queryFn: () => fetchProjectResults(uid, pid, token, ownerId, shareId),
  });
};

export const useGetSharedProject = (shareId: string, token: string) => {
  return useQuery({
    queryKey: ["sharedProject", shareId, token],
    queryFn: () => fetchSharedProject(shareId, token),
    enabled: !!shareId && !!token,
  });
};

export const useResolveShareLink = (shareId?: string | null) => {
  return useQuery({
    queryKey: ["resolveShareLink", shareId],
    queryFn: () => resolveShareLink(shareId as string),
    enabled: !!shareId,
    staleTime: 30_000,
    retry: false,
  });
};
