# ==============================================================================
# Protobuf Generation
# ==============================================================================
.PHONY: proto generate-protos update-protos clean-protos

proto: submodule-update generate-protos ## Update proto submodules and generate gRPC code (recommended workflow)

generate-protos: ## Generate Python gRPC stubs from ALL proto submodules under protos/*/protos
	@$(call title,Generating protobuf files for all services)
	@$(EHR_PROTOS)/scripts/generate_protos.sh $(PYTHON)
	@$(call ok,Protobuf files generated for all services)

clean-protos: ## Clean generated protobuf files
	@$(call title,Cleaning generated protobuf files)
	@find core/grpc -name "*_pb2.py" -delete
	@find core/grpc -name "*_pb2.pyi" -delete
	@find core/grpc -name "*_pb2_grpc.py" -delete
	@$(call ok,Generated protobuf files cleaned)

