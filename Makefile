IMAGE     := sauria-systemc-dev:latest
CONTAINER := sauria-dev
BUILD_DIR := build

.PHONY: docker-build dev test-sim-build clean test

docker-build:
	docker build -t $(IMAGE) .

dev:
	docker run -it --rm \
	  --name $(CONTAINER) \
	  -v $(PWD):/workspace/sauria-systemc-simulator \
	  $(IMAGE)

SAURIA_ROOT    := $(CURDIR)/3rdparty/sauria
SAURIA_SIM_DIR := $(SAURIA_ROOT)/test/verilator

# Compile Verilator RTL simulator
test-sim-build:
	RTL_DIR=$(SAURIA_ROOT)/RTL \
	PULP_DIR=$(SAURIA_ROOT)/pulp_platform \
	version=FP16_8x16 \
	$(MAKE) -C $(SAURIA_SIM_DIR)

$(BUILD_DIR)/Makefile:
	cmake -S . -B $(BUILD_DIR)

test: $(BUILD_DIR)/Makefile
	cmake --build $(BUILD_DIR)
	ctest --test-dir $(BUILD_DIR) --output-on-failure

clean:
	docker rmi $(IMAGE)
	rm -rf $(BUILD_DIR)