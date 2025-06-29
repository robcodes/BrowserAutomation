/**
 * Deep hit-test under viewport point (x,y), drilling into same-origin
 * iframes and *open* shadow-roots. Each result includes:
 *   • element     – the DOM node
 *   • path        – human-readable trail (document > iframe … ::shadow > …)
 *   • area        – bounding-rect width × height (px²)
 *   • visibility  – comprehensive visibility information
 *
 * The returned list is sorted ASC by area (smallest first).
 */
function deepElementsFromPointSorted(root, x, y, options = {}) {
	const {
		includeHidden = true, // include elements that aren't actually visible
		checkPartialVisibility = true, // check multiple points within elements
		maxDepth = 50, // prevent infinite recursion
	} = options;

	const queue = [{ root, x, y, path: "document", depth: 0 }];
	const visited = new WeakSet();
	const results = [];

	// Helper to create readable element description
	const describe = (el) => {
		const tag = (el.tagName || "").toLowerCase();
		const id = el.id ? `#${el.id}` : "";
		const cls = el.classList?.length ? "." + [...el.classList].join(".") : "";
		return tag + id + cls;
	};

	// Check if element is actually visible at the given point
	const checkVisibilityAtPoint = (element, px, py) => {
		try {
			const topElement = element.ownerDocument.elementFromPoint(px, py);
			if (!topElement) return false;

			// Check if the element is the topmost or contains the topmost element
			return topElement === element || element.contains(topElement);
		} catch {
			return false;
		}
	};

	// Check visibility across multiple points within the element
	const checkPartialVisibilityDetailed = (element, centerX, centerY) => {
		const rect = element.getBoundingClientRect();
		if (rect.width <= 0 || rect.height <= 0)
			return { visible: false, points: [] };

		const margin = 2; // pixels from edge
		const points = [
			{
				x: Math.max(rect.left + margin, rect.left),
				y: Math.max(rect.top + margin, rect.top),
				name: "top-left",
			},
			{
				x: Math.min(rect.right - margin, rect.right),
				y: Math.max(rect.top + margin, rect.top),
				name: "top-right",
			},
			{ x: centerX, y: centerY, name: "center" },
			{
				x: Math.max(rect.left + margin, rect.left),
				y: Math.min(rect.bottom - margin, rect.bottom),
				name: "bottom-left",
			},
			{
				x: Math.min(rect.right - margin, rect.right),
				y: Math.min(rect.bottom - margin, rect.bottom),
				name: "bottom-right",
			},
		];

		const visiblePoints = points.filter((point) => {
			// Make sure point is within viewport
			if (
				point.x < 0 ||
				point.y < 0 ||
				point.x >= window.innerWidth ||
				point.y >= window.innerHeight
			) {
				return false;
			}
			return checkVisibilityAtPoint(element, point.x, point.y);
		});

		return {
			visible: visiblePoints.length > 0,
			visiblePoints: visiblePoints.map((p) => p.name),
			totalPoints: points.length,
			visibleCount: visiblePoints.length,
		};
	};

	// Get comprehensive visibility information
	const getVisibilityInfo = (element, cx, cy, zIndex) => {
		const rect = element.getBoundingClientRect();
		const styles = element.ownerDocument.defaultView.getComputedStyle(element);

		const hasZeroSize = rect.width === 0 || rect.height === 0;
		const isStyleHidden =
			styles.display === "none" || styles.visibility === "hidden";
		const isTransparent = parseFloat(styles.opacity) === 0;
		const isOffscreen =
			rect.bottom < 0 ||
			rect.top > window.innerHeight ||
			rect.right < 0 ||
			rect.left > window.innerWidth;

		let partialVisibility = {
			visible: false,
			visiblePoints: [],
			totalPoints: 0,
			visibleCount: 0,
		};
		if (
			checkPartialVisibility &&
			!hasZeroSize &&
			!isStyleHidden &&
			!isTransparent
		) {
			partialVisibility = checkPartialVisibilityDetailed(element, cx, cy);
		}

		const isTopmost =
			zIndex === 0 && !hasZeroSize && !isStyleHidden && !isTransparent;
		const isActuallyVisible =
			isTopmost || (checkPartialVisibility && partialVisibility.visible);

		return {
			isTopmost,
			isActuallyVisible,
			hasZeroSize,
			isStyleHidden,
			isTransparent,
			isOffscreen,
			zIndex,
			computedZIndex: styles.zIndex,
			opacity: parseFloat(styles.opacity),
			display: styles.display,
			visibility: styles.visibility,
			partialVisibility,
			// Summary flags
			isCompletelyHidden: hasZeroSize || isStyleHidden || isTransparent,
			isPotentiallyVisible:
				!hasZeroSize && !isStyleHidden && !isTransparent && !isOffscreen,
		};
	};

	while (queue.length) {
		const { root: ctx, x: cx, y: cy, path, depth } = queue.pop();

		if (depth > maxDepth) {
			console.warn(`Max depth ${maxDepth} reached for path: ${path}`);
			continue;
		}

		if (visited.has(ctx)) continue;
		visited.add(ctx);

		let elementsAtPoint;
		try {
			elementsAtPoint = ctx.elementsFromPoint(cx, cy);
		} catch (error) {
			console.warn(`Failed to get elements from point in ${path}:`, error);
			continue;
		}

		elementsAtPoint.forEach((el, zIndex) => {
			try {
				const { width, height } = el.getBoundingClientRect();
				const area = width * height;
				const elPath = `${path} > ${describe(el)}`;

				const visibility = getVisibilityInfo(el, cx, cy, zIndex);

				// Skip hidden elements if not requested
				if (!includeHidden && !visibility.isActuallyVisible) {
					return;
				}

				results.push({
					element: el,
					path: elPath,
					area,
					visibility,
				});

				/* ---- dive into same-origin iframe ----------------------- */
				if (el.tagName === "IFRAME") {
					let doc;
					try {
						doc = el.contentDocument;
					} catch {
						/* cross-origin iframe - cannot access */
					}

					if (doc) {
						const iframeRect = el.getBoundingClientRect();
						// Transform coordinates to iframe's coordinate system
						const iframeX = cx - iframeRect.left;
						const iframeY = cy - iframeRect.top;

						// Only traverse if point is within iframe bounds
						if (
							iframeX >= 0 &&
							iframeY >= 0 &&
							iframeX < iframeRect.width &&
							iframeY < iframeRect.height
						) {
							queue.push({
								root: doc,
								x: iframeX,
								y: iframeY,
								path: elPath,
								depth: depth + 1,
							});
						}
					}
					return; // Don't check for shadow roots on iframes
				}

				/* ---- dive into open shadow-root ------------------------- */
				if (el.shadowRoot) {
					queue.push({
						root: el.shadowRoot,
						x: cx,
						y: cy,
						path: `${elPath}::shadow`,
						depth: depth + 1,
					});
				}
			} catch (error) {
				console.warn(`Error processing element in ${path}:`, error);
			}
		});
	}

	// Sort by area (smallest first)
	results.sort((a, b) => a.area - b.area);
	return results;
}

/**
 * Convenience function that returns only visible elements
 */
function deepVisibleElementsFromPointSorted(root, x, y, options = {}) {
	return deepElementsFromPointSorted(root, x, y, {
		...options,
		includeHidden: false,
	});
}

/**
 * Pretty print results with visibility information
 */
function printElementResults(results, options = {}) {
	const { showHidden = true, showDetails = false } = options;

	if (!results || results.length === 0) {
		console.log("❌ No elements found at the specified coordinates");
		return { summary: "No elements found", visibleCount: 0, totalCount: 0 };
	}

	console.log(`\n📍 Found ${results.length} elements:\n`);

	let visibleCount = 0;
	const output = [];

	results.forEach((result, index) => {
		const { path, area, visibility } = result;
		const {
			isActuallyVisible,
			isTopmost,
			isCompletelyHidden,
			partialVisibility,
		} = visibility;

		if (!showHidden && !isActuallyVisible) return;
		if (isActuallyVisible) visibleCount++;

		let status = "";
		if (isTopmost) status = "👁️  TOPMOST";
		else if (isActuallyVisible) status = "✅ VISIBLE";
		else if (isCompletelyHidden) status = "❌ HIDDEN";
		else status = "🫥 OCCLUDED";

		const areaStr = area.toFixed(0).padStart(8);
		const zIndexStr = `z:${visibility.zIndex}`.padStart(4);

		const line = `${areaStr}px² ${zIndexStr} ${status} ${path}`;
		console.log(line, result.element); // Include the DOM element for hover highlighting
		output.push(line);

		if (showDetails) {
			const details = [];
			if (partialVisibility.visible) {
				const visPoints = partialVisibility.visiblePoints.join(", ");
				const coverage = `${partialVisibility.visibleCount}/${partialVisibility.totalPoints}`;
				details.push(`Visible at: ${visPoints} (${coverage} points)`);
			}
			if (visibility.opacity < 1) details.push(`opacity: ${visibility.opacity}`);
			if (visibility.computedZIndex !== "auto")
				details.push(`z-index: ${visibility.computedZIndex}`);
			if (details.length > 0) {
				const detailLine = `           └─ ${details.join(" | ")}`;
				console.log(detailLine);
				output.push(detailLine);
			}
		}
	});

	const summary = `\n📊 Summary: ${visibleCount} visible / ${results.length} total elements`;
	console.log(summary);

	return {
		summary: `${visibleCount} visible / ${results.length} total`,
		visibleCount,
		totalCount: results.length,
		output: output.join("\n"),
	};
}

/**
 * Quick visibility summary - just the key info
 */
function quickVisibilitySummary(results) {
	const visible = results.filter((r) => r.visibility.isActuallyVisible);
	const topmost = results.filter((r) => r.visibility.isTopmost);
	const hidden = results.filter((r) => r.visibility.isCompletelyHidden);

	console.log(`\n🎯 Quick Summary:`);
	console.log(`   👁️  Topmost: ${topmost.length}`);
	console.log(`   ✅ Visible: ${visible.length}`);
	console.log(`   ❌ Hidden: ${hidden.length}`);
	console.log(
		`   🫥 Occluded: ${results.length - visible.length - hidden.length}`,
	);

	if (topmost.length > 0) {
		console.log(`\n🏆 Topmost element:`);
		topmost.forEach((r) => {
			console.log(`   ${r.area.toFixed(0)}px² ${r.path}`, r.element);
		});
	}

	return {
		visible,
		topmost,
		hidden,
		occluded: results.filter(
			(r) => !r.visibility.isActuallyVisible && !r.visibility.isCompletelyHidden,
		),
	};
}

// Example usage:
if (typeof window !== "undefined") {
	// Example 1: Get all elements (including hidden ones)
	const allHits = deepElementsFromPointSorted(document, 588, 12);
	printElementResults(allHits, { showDetails: true });

	// Example 2: Get only visible elements
	const visibleHits = deepVisibleElementsFromPointSorted(document, 588, 12);
	console.log(`\n🎯 Only visible elements (${visibleHits.length}):`);
	printElementResults(visibleHits, { showHidden: false });

	// Example 3: Access detailed visibility info
	allHits.forEach((hit) => {
		if (hit.visibility.isActuallyVisible) {
			console.log(`✅ ${hit.path}`, {
				area: hit.area,
				isTopmost: hit.visibility.isTopmost,
				partiallyVisible: hit.visibility.partialVisibility.visible,
				visiblePoints: hit.visibility.partialVisibility.visiblePoints,
			});
		}
	});
}
