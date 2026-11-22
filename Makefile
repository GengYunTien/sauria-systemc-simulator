IMAGE     := sauria-systemc-dev:latest
CONTAINER := sauria-dev
BUILD_DIR := build

.PHONY: docker-build dev clean test

docker-build:
	docker build -t $(IMAGE) .

dev:
	docker run -it --rm \
	  --name $(CONTAINER) \
	  -v $(PWD):/workspace/sauria-systemc-simulator \
	  $(IMAGE)

$(BUILD_DIR)/Makefile:
	cmake -S . -B $(BUILD_DIR)

test: $(BUILD_DIR)/Makefile
	cmake --build $(BUILD_DIR)
	ctest --test-dir $(BUILD_DIR) --output-on-failure

clean:
	docker rmi $(IMAGE)
	rm -rf $(BUILD_DIR)