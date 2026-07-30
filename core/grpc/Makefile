# ==============================================================================
# gRPC
# ==============================================================================
.PHONY: run-grpc-server generate-grpc-token

run-grpc-server: ## Run gRPC server
	$(call title,Running gRPC server on port $(GRPC_PORT))
	$(MANAGE) grpcserver --port $(GRPC_PORT) --autoreload

generate-grpc-token: ## Generate gRPC JWT token for testing
	$(call title,Generating gRPC JWT token)
	$(MANAGE) generate_grpc_token

