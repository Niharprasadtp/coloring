-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "public";

-- CreateEnum
CREATE TYPE "OrderStatus" AS ENUM ('AWAITING_UPLOAD', 'PROCESSING', 'COMPLETED', 'FAILED');

-- CreateTable
CREATE TABLE "orders" (
    "id" TEXT NOT NULL,
    "receipt_id" BIGINT NOT NULL,
    "shop_id" BIGINT NOT NULL,
    "buyer_email" TEXT NOT NULL,
    "upload_token" TEXT NOT NULL,
    "status" "OrderStatus" NOT NULL DEFAULT 'AWAITING_UPLOAD',
    "pdf_path" TEXT,
    "error" TEXT,
    "etsy_shipped_at" TIMESTAMP(3),
    "etsy_error" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "orders_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "etsy_tokens" (
    "id" INTEGER NOT NULL DEFAULT 1,
    "access_token" TEXT NOT NULL,
    "refresh_token" TEXT NOT NULL,
    "expires_at" TIMESTAMP(3) NOT NULL,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "etsy_tokens_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "orders_receipt_id_key" ON "orders"("receipt_id");

-- CreateIndex
CREATE UNIQUE INDEX "orders_upload_token_key" ON "orders"("upload_token");

