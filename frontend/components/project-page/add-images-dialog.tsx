"use client";

import { useRef, useState } from "react";
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import ImageSubmissionArea from "../image-submission-area";
import { LoaderCircle, Plus } from "lucide-react";
import { useAddProjectImages } from "@/lib/mutations/projects";
import { createBlobUrlFromFile } from "@/lib/utils";
import { useProjectInfo } from "@/providers/project-provider";
import { useSession } from "@/providers/session-provider";
import { useToast } from "@/hooks/use-toast";
import { useSearchParams } from "next/navigation";
import { getErrorMessage } from "@/lib/error-messages";

export function AddImagesDialog() {
  const [open, setOpen] = useState(false);
  const [images, setImages] = useState<string[]>([]);
  const [imageFiles, setImageFiles] = useState<File[]>([]);
  const [progress, setProgress] = useState<number | null>(null);
  const uploadController = useRef<AbortController | null>(null);
  const { toast } = useToast();

  const { _id: pid, version} = useProjectInfo();
  const session = useSession();

  // use the same owner/share as the project query, otherwise the cache key
  // differs and the new media only shows up after a page refresh
  const searchParams = useSearchParams();
  const ownerId = searchParams.get("owner") ?? session.user._id;
  const shareId = searchParams.get("share") ?? undefined;

  const addImages = useAddProjectImages(
    session.user._id,
    pid as string,
    session.token,
    ownerId,
    shareId,
  );

  function onDrop(files: File[]) {
    files.map(async (file) => {
      const url = await createBlobUrlFromFile(file);
      setImages((prevImages) => [...prevImages, url]);
    });
    setImageFiles(files);
  }

  function handleAdd() {
    const controller = new AbortController();
    uploadController.current = controller;
    setProgress(null);
    addImages.mutate(
      {
        images: imageFiles,
        projectVersion: version,
        signal: controller.signal,
        onProgress: setProgress,
      },
      {
        onSuccess: () => {
          uploadController.current = null;
          setProgress(null);
          toast({
            title: "Media added successfully.",
          });
          setOpen(false);
        },
        onError: (error) => {
          uploadController.current = null;
          setProgress(null);
          if (controller.signal.aborted) return;
          const { title, description } = getErrorMessage("project-upload", error);
          toast({
            title,
            description,
            variant: "destructive",
          });
        },
      },
    );
  }

  return (
    <Dialog open={open} onOpenChange={(next) => {
      if (!next) uploadController.current?.abort();
      setOpen(next);
    }}>
      <DialogTrigger asChild>
        <Button className="inline-flex" variant="outline">
          <Plus /> Import
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Import</DialogTitle>
          <DialogDescription>
            Add images or videos to your project.
          </DialogDescription>
        </DialogHeader>
        <ImageSubmissionArea onDrop={onDrop} />
        {addImages.isPending && progress !== null && (
          <p role="status">Uploading video: {progress}%{progress === 100 ? " — validating" : ""}</p>
        )}
        <DialogFooter>
          {addImages.isPending && (
            <Button type="button" variant="outline" onClick={() => uploadController.current?.abort()}>
              Cancel upload
            </Button>
          )}
          <Button
            onClick={handleAdd}
            disabled={images.length === 0 || addImages.isPending}
            className="inline-flex items-center gap-1"
          >
            <span>Add</span>
            {addImages.isPending && (
              <LoaderCircle className="size-[1em] animate-spin" />
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
