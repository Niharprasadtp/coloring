-- AlterTable
ALTER TABLE "orders" DROP COLUMN "pdf_path",
ADD COLUMN     "formats" TEXT[] DEFAULT ARRAY[]::TEXT[],
ADD COLUMN     "outputs" JSONB,
ADD COLUMN     "progress" INTEGER NOT NULL DEFAULT 0,
ADD COLUMN     "progress_message" TEXT;

