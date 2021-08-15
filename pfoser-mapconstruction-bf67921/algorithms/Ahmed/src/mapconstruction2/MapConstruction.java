/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package mapconstruction2;

/**
 *
 * @author peyman
 */

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.OutputStreamWriter;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.StringTokenizer;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.lang.instrument.Instrumentation;


class BadInputTrajectory extends Exception { 
    public BadInputTrajectory(String errorMessage) {
        super(errorMessage);
    }
}


class PoseFile {
	String curveName;
	ArrayList<Vertex> curve;

	PoseFile() {
		this.curveName = "";
		this.curve = new ArrayList<Vertex>();
	}

	PoseFile(String curveName, ArrayList<Vertex> curve) {
		this.curveName = curveName;
		this.curve = curve;
	}

	public String getCurveName() {
		return curveName;
	}

	public ArrayList<Vertex> getPose() {
		return curve;
	}

	public double getLength() {
		double length = 0;
		for (int i = 1; i < curve.size(); i++) {
			length = length + curve.get(i - 1).dist(curve.get(i));
		}
		return length;
	}

        public static List<PoseFile> readFolder(File folder, boolean hasAltitude) {
            List<PoseFile> poseFiles = new ArrayList<PoseFile>();
            int counter = 0;
            for (File file : folder.listFiles()) {
                try {
                    String str = "";
                    String headers = "";
                    String timestamp = "";
                    BufferedReader in = new BufferedReader(new FileReader(file.getAbsolutePath()));
                    headers = in.readLine();
                    str = in.readLine();
                    StringTokenizer strToken = new StringTokenizer(str);
                    PoseFile poseFile = new PoseFile();
                    double x, y, z;
                    int pre_routeId, route_id;
                    route_id = Integer.parseInt(strToken.nextToken(","));
                    while ((str = in.readLine()) != null) {
                        pre_routeId = route_id;
                        x = Double.parseDouble(strToken.nextToken(","));
                        y = Double.parseDouble(strToken.nextToken(","));
                        z = Double.parseDouble(strToken.nextToken(","));
                        timestamp = strToken.nextToken(",");
                        Vertex newPoint = new Vertex(x, y, z, timestamp);
                        poseFile.curve.add(newPoint);
                        strToken = new StringTokenizer(str);
                        route_id = Integer.parseInt(strToken.nextToken(","));
                        if (route_id != pre_routeId){
                            if (poseFile.curve.size() > 0){
                                counter ++;
                                poseFile.curveName = String.valueOf(pre_routeId);
                                poseFiles.add(poseFile);
                            }
                            poseFile = new PoseFile();
                        }	
                    }
                    in.close();

                } catch (Exception e) {
                        e.printStackTrace();
                }
            }
            return poseFiles;
	}
}

/**
 * An object that takes a set of poses as input, construct graph and write two
 * files one for vertices and one for edges.
 */
public class MapConstruction {

	public static int curveid; // counter for pose
	public static String curveName; // file name for the pose

	private static final Logger logger = Logger.getAnonymousLogger();

	/**
	 * Writes the constructed map into files.
	 */

	public static void writeToFile(List<Vertex> vList, String fileName) {

		try {
			int count = 0;
			BufferedWriter bwedges = new BufferedWriter(new FileWriter(fileName
					+ "edges.txt"));
			BufferedWriter bvertex = new BufferedWriter(new FileWriter(fileName
					+ "vertices.txt"));
			

			for (int i = 0; i < vList.size(); i++) {
				Vertex v = vList.get(i);
				bvertex.write(i + "," + v.getX() + "," + v.getY() +","+ v.getZ() + "\n");

				for (int j = 0; j < v.getDegree(); j++) {

					if (i != v.getAdjacentElementAt(j)) {
						
						bwedges.write(count + "," + i + ","
								+ v.getAdjacentElementAt(j) + "\n");
						
						count++;
					}
				}
			}
			
			
			bwedges.close();
			bvertex.close();
		} catch (Exception ex) {
			System.out.println(ex.toString());
		}
	}

	/**
	 * Computes interval on edge e for a line segment consists of
	 * (currentIndex-1)-th and currentIndex-th vertices of pose and return true
	 * if edge e has a part of white interval else false.
	 */

	public int isWhiteInterval(Edge edge, List<Vertex> pose,
			int currentIndex, double eps, double altEps) {
		Line line = new Line(pose.get(currentIndex - 1), pose.get(currentIndex));

		if (Math.abs(line.avgAltitude() - edge.getLine().avgAltitude()) <= altEps) {
			return line.pIntersection(edge, eps);
		} else {
			return 0;
		}
	}

	/**
	 * Sets corresponding interval endpoints on Edge.
	 */
	public void setEndPointsOnEdge(Edge edge, int startIndex, int endIndex,
			double cstart, double vstart) {
		edge.setCurveStartIndex(startIndex);
		edge.setCurveStart(startIndex + cstart);
		edge.setEdgeStart(vstart);

		edge.setCurveEnd(endIndex - 1 + edge.getCurveEnd());
		edge.setCurveEndIndex(endIndex);
	}

	/**
	 * Scans for next white interval on an Edge starting from index newstart of
	 * pose.
	 */
	public int computeNextInterval(Edge edge, List<Vertex> pose, int newstart,
			double eps, double altEps) {

		// Compute next white interval on edge.
		boolean first = true;
		boolean debug = false;

		int startIndex = 0;
		double cstart = 0, vstart = 0;

		if (newstart >= pose.size()) {
			edge.setCurveEndIndex(pose.size());
			edge.setDone(true);
			return 1;
		}

		for (int i = newstart; i < pose.size(); i++) {
			int result = isWhiteInterval(edge, pose, i, eps, altEps);

			// first = true means we are still looking for our first interval
			// starting from newstart.
			// !result indicate Line(pose.get(i), pose.get(i+1)) doesn't contain
			// white interval.
			// we can just ignore if(first && !result).
                        if (result == 2){
                            return 0;
                        } else if (first && (result == 1)) {
				// first segment on the white interval
				first = false;
				startIndex = i - 1;
				cstart = edge.getCurveStart();
				vstart = edge.getEdgeStart();

				// if the white interval ends within the same segment
				if (edge.getCurveEnd() < 1) {
					this.setEndPointsOnEdge(edge, startIndex, i, cstart, vstart);
					return 1;
				}
			} else if (!first && (result == 1)) {
				// not the first segment on the white interval
				if (edge.getCurveEnd() < 1) {
					// if the white interval ends within that segment
					this.setEndPointsOnEdge(edge, startIndex, i, cstart, vstart);
					return 1;
				}
			} else if (!first && (result == 0)) {
				// the white interval ends at 1.0 of previous segment
				this.setEndPointsOnEdge(edge, startIndex, i, cstart, vstart);
				return 1;
			}
		}

		if (first) {
			// if the last segment on the curve is the first segment of that
			// interval
			edge.setCurveEndIndex(pose.size());
			edge.setDone(true);
		} else {
			edge.setCurveStartIndex(startIndex);
			edge.setCurveStart(startIndex + cstart);
			edge.setEdgeStart(vstart);

			edge.setCurveEnd(pose.size() - 2 + edge.getCurveEnd());
			edge.setCurveEndIndex(pose.size() - 2);
		}

		return 1;
	}

	/**
	 * Updates constructedMap by adding an Edge. Detail description of the
	 * algorithm is in the publication.
	 */
	public void updateMap(List<Vertex> constructedMap,
			Map<String, Integer> map, Edge edge) {

		// update the map by adding a new edge
		Vertex v;
		int parent = -1;
		int child = -1;

		String keyParent = edge.getVertex1().toString();
		String keyChild = edge.getVertex2().toString();
		// find the index of parent node
		if (map.containsKey(keyParent)) {
			parent = map.get(keyParent).intValue();
		} else {
			v = edge.getVertex1();
			constructedMap.add(v);
			parent = constructedMap.indexOf(v);
			map.put(keyParent, parent);
		}
		// find the index of child node
		if (map.containsKey(keyChild)) {
			child = map.get(keyChild).intValue();
		} else {
			v = edge.getVertex2();
			constructedMap.add(v);
			child = constructedMap.indexOf(v);
			map.put(keyChild, child);
		}
		// update the map
		if (parent == -1 || child == -1) {
			logger.log(Level.SEVERE, "inconsistent graph child, parent :"
					+ child + ", " + parent);
		} else if (parent != child) {

			constructedMap.get(parent).addElementAdjList(child);
			constructedMap.get(child).addElementAdjList(parent);

			logger.log(Level.FINEST, "child, parent :" + child + ", " + parent);
			logger.log(Level.FINEST, "child, parent :" + parent + ", " + child);

		}
	}

	/**
	 * Adds a split point on an Edge.
	 * 
	 * @param newVertexPosition
	 *            represents position of a new Vertex
	 */
	public void edgeSplit(List<Vertex> constructedMap,
			Map<String, Integer> map, Edge edge, double newVertexPosition) {

		Vertex v1 = edge.getVertex1();
		Vertex v2 = edge.getVertex2();

		String key1 = v1.toString();
		String key2 = v2.toString();

		// call of this method always after updateMap which ensures
		// map.containsKey(key1) is
		// always true.
		int index1 = map.get(key1).intValue();
		int index2 = map.get(key2).intValue();

		Vertex v = edge.getLine().getVertex(newVertexPosition);

		// splitting an edge on split point vertex v

		String key = v.toString();

		int index = map.get(key).intValue();

		if (index == index1 || index == index2) {
			return;
		}

		logger.log(Level.FINER, "Index = " + index1 + " " + index2 + " "
				+ index);

		edge.addSplit(newVertexPosition, index);
	}

	/**
	 * Commits edge splitting listed in List<Integer> Edge.edgeSplitVertices.
	 */

	public void commitEdgeSplits(List<Edge> edges, Map<String, Integer> map,
			List<Vertex> graph) {

		if (edges.size() != 2) {
			// logger.log(Level.SEVERE, "created.");
			return;
		}

		Edge edge = edges.get(0);

		for (int i = 0; i < edges.get(1).getEdgeSplitPositions().size(); i++) {
			double newPosition = 1 - edges.get(1).getEdgeSplitPositions()
					.get(i).doubleValue();
			edge.addSplit(newPosition,
					edges.get(1).getEdgeSplitVertices().get(i));
		}

		List<Integer> edgeVertexSplits = edge.getEdgeSplitVertices();
		int splitSize = edgeVertexSplits.size();

		if (splitSize == 0) {
			return;
		}

		Vertex v1 = edge.getVertex1();
		Vertex v2 = edge.getVertex2();

		String key1 = v1.toString();
		String key2 = v2.toString();

		int index1 = map.get(key1).intValue();
		int index2 = map.get(key2).intValue();

		boolean updateV1 = false, updateV2 = false;

		logger.log(Level.FINER, "commitEdgeSplits " + splitSize);

		for (int i = 0; i < v1.getDegree(); i++) {
			if (v1.getAdjacentElementAt(i) == index2) {
				v1.setAdjacentElementAt(i, edgeVertexSplits.get(0).intValue());
				graph.get(edgeVertexSplits.get(0).intValue())
						.addElementAdjList(index1);
				updateV1 = true;
			}
		}

		for (int i = 0; i < v2.getDegree(); i++) {
			if (v2.getAdjacentElementAt(i) == index1) {
				v2.setAdjacentElementAt(i, edgeVertexSplits.get(splitSize - 1)
						.intValue());
				graph.get(edgeVertexSplits.get(splitSize - 1).intValue())
						.addElementAdjList(index2);
				updateV2 = true;
			}
		}

		for (int i = 0; i < splitSize - 1; i++) {
			int currentVertex = edgeVertexSplits.get(i).intValue();
			int nextVertex = edgeVertexSplits.get(i + 1).intValue();
			graph.get(currentVertex).addElementAdjList(nextVertex);
			graph.get(nextVertex).addElementAdjList(currentVertex);
		}
		if (!(updateV1 && updateV2)) {
			logger.log(Level.SEVERE, "inconsistent graph: (" + splitSize + ")"
					+ index1 + " " + index2 + " "
					+ v1.getAdjacencyList().toString() + " "
					+ v2.getAdjacencyList().toString());
		}
	}

	/**
	 * Commits edge splitting for all edges.
	 */

	public void commitEdgeSplitsAll(List<Vertex> constructedMap,
			Map<String, Integer> map, Map<String, ArrayList<Edge>> siblingMap,
			List<Edge> edges) {
		for (int i = 0; i < edges.size(); i++) {
			String key1 = edges.get(i).getVertex1().toString() + " "
					+ edges.get(i).getVertex2().toString();
			String key2 = edges.get(i).getVertex2().toString() + " "
					+ edges.get(i).getVertex1().toString();

			ArrayList<Edge> siblings1, siblings2;
			if (siblingMap.containsKey(key1))
				siblings1 = siblingMap.get(key1);
			else {
				siblings1 = new ArrayList<Edge>();
			}
			if (siblingMap.containsKey(key2))
				siblings2 = siblingMap.get(key2);
			else {
				siblings2 = new ArrayList<Edge>();
			}
			if (siblings1.size() != 0) {
				this.commitEdgeSplits(siblings1, map, constructedMap);
				siblingMap.remove(key1);
			} else if (siblings2.size() != 0) {
				this.commitEdgeSplits(siblings2, map, constructedMap);
				siblingMap.remove(key2);
			}
		}
	}

	/**
	 * Adds a portion of a pose as edges into constructedMap.
	 */

	public void addToGraph(List<Vertex> constructedMap, List<Vertex> pose,
			Map<String, Integer> map, int startIndex, int endIndex) {
		for (int i = startIndex; i < endIndex; i++) {
			this.updateMap(constructedMap, map,
					new Edge(pose.get(i), pose.get(i + 1)));
		}

	}

	/**
	 * Updates siblingHashmap for an edge.
	 */

	public void updateSiblingHashMap(Map<String, ArrayList<Edge>> siblingMap,
			Edge edge) {
		String key1 = edge.getVertex1().toString() + " "
				+ edge.getVertex2().toString();
		String key2 = edge.getVertex2().toString() + " "
				+ edge.getVertex1().toString();
		Collection<Edge> siblings1, siblings2;
		if (siblingMap.containsKey(key1)) {
			siblings1 = siblingMap.get(key1);
		} else {
			siblings1 = new ArrayList<Edge>();
		}
		if (siblingMap.containsKey(key1)) {
			siblings2 = siblingMap.get(key2);
		} else {
			siblings2 = new ArrayList<Edge>();
		}

		if (siblings1.size() == 0 && siblings2.size() == 0) {
			siblingMap.put(key1, new ArrayList<Edge>());
			siblingMap.get(key1).add(edge);
		} else if (siblings1.size() != 0) {
			siblings1.add(edge);
		} else if (siblings2.size() != 0) {
			siblings2.add(edge);
		}
	}

	/**
	 * Update the map for a pose/curve. Definition of black and white interval.
	 */
	// @TODO(mahmuda): extract some shorter well-named methods.
	public int mapConstruction(List<Vertex> constructedMap, List<Edge> edges,
			Map<String, Integer> map, List<Vertex> pose, double eps,
			double altEps) {

		PriorityQueue<Edge> pq = new PriorityQueue<Edge>();

		for (int i = 0; i < edges.size(); i++) {
			int result = this.computeNextInterval(edges.get(i), pose, 1, eps, altEps);
                        if (result == 0) {
                            return 0;
                        }
			if (!edges.get(i).getDone()) {
				pq.add(edges.get(i));
			}
		}
		try {

			// The whole curve will be added as an edge because no white
			// interval

			if (pq.isEmpty()) {

				logger.log(Level.FINER, MapConstruction.curveName
						+ " inserted as an edge");

				this.addToGraph(constructedMap, pose, map, 0, pose.size() - 1);

				logger.log(Level.FINER, MapConstruction.curveName
						+ " inserted as an edge");
				return 1;
			}

			Edge edge = pq.poll();

			double cend = edge.getCurveEnd();
			Edge cedge = edge;

			// There is a black interval until edge.curveStart

			if (edge.getCurveStart() > 0) {

				logger.log(Level.FINER, MapConstruction.curveName
						+ " inserted as an edge until " + edge.getCurveStart());

				int index = (int) Math.floor(edge.getCurveStart());

				this.addToGraph(constructedMap, pose, map, 0, index);

				Line newLine = new Line(pose.get(index), pose.get(index + 1));
				double t = edge.getCurveStart()
						- Math.floor(edge.getCurveStart());
				this.updateMap(constructedMap, map, new Edge(pose.get(index),
						newLine.getVertex(t)));

				this.updateMap(constructedMap, map,
						new Edge(newLine.getVertex(t), edge.getLine()
								.getVertex(edge.getEdgeStart())));
				this.edgeSplit(constructedMap, map, edge, edge.getEdgeStart());
			}

			// the while loop will search through all the intervals until we
			// reach the end of the pose

			while (cend < pose.size()) {

				logger.log(Level.FINEST, MapConstruction.curveName
						+ " has white interval " + edge.getCurveStart() + " "
						+ edge.getCurveEnd() + " " + cend);

				if (cend < edge.getCurveEnd()) {
					cend = edge.getCurveEnd();
					cedge = edge;
				}

				if (edge.getCurveEnd() == pose.size() - 1) {
					logger.log(Level.FINER, MapConstruction.curveName
							+ " processing completed.");
					return 1;
				}

				int result = this.computeNextInterval(edge, pose,
						edge.getCurveEndIndex() + 1, eps, altEps);
                                if (result == 0) {
                                    return 0;
                                }

				if (!edge.getDone()) {
					pq.add(edge);
				}

				if (pq.isEmpty()) {
					logger.log(Level.FINER, MapConstruction.curveName
							+ " inserted as an edge from " + cend + " to end");

					int index = (int) Math.floor(cend);
					Line newLine = new Line(pose.get(index),
							pose.get(index + 1));
					double t = cend - Math.floor(cend);
					this.updateMap(
							constructedMap,
							map,
							new Edge(cedge.getLine().getVertex(
									cedge.getEdgeEnd()), newLine.getVertex(t)));
					this.edgeSplit(constructedMap, map, cedge,
							cedge.getEdgeEnd());
					this.updateMap(constructedMap, map,
							new Edge(newLine.getVertex(t), pose.get(index + 1)));
					this.addToGraph(constructedMap, pose, map, index + 1,
							pose.size() - 1);

					return 1;
				}

				edge = pq.poll();

				if (edge.getCurveStart() > cend) {
					logger.log(Level.FINER, MapConstruction.curveName
							+ " inserted as an edge from " + cend + " to "
							+ edge.getCurveStart());

					// need to add rest of the line segment

					int index = (int) Math.floor(cend);
					int indexStart = (int) Math.floor(edge.getCurveStart());
					Line newLine = new Line(pose.get(index),
							pose.get(index + 1));
					double t = cend - Math.floor(cend);

					this.updateMap(
							constructedMap,
							map,
							new Edge(cedge.getLine().getVertex(
									cedge.getEdgeEnd()), newLine.getVertex(t)));
					this.edgeSplit(constructedMap, map, cedge,
							cedge.getEdgeEnd());

					if (index == indexStart) {
						this.updateMap(
								constructedMap,
								map,
								new Edge(newLine.getVertex(t),
										newLine.getVertex(edge.getCurveStart()
												- index)));
						index = (int) Math.floor(edge.getCurveStart());
						newLine = new Line(pose.get(index), pose.get(index + 1));
						t = edge.getCurveStart()
								- Math.floor(edge.getCurveStart());
					} else {
						this.updateMap(
								constructedMap,
								map,
								new Edge(newLine.getVertex(t), pose
										.get(index + 1)));

						this.addToGraph(constructedMap, pose, map, index + 1,
								(int) Math.floor(edge.getCurveStart()));
						index = (int) Math.floor(edge.getCurveStart());
						newLine = new Line(pose.get(index), pose.get(index + 1));
						t = edge.getCurveStart()
								- Math.floor(edge.getCurveStart());
						this.updateMap(constructedMap, map,
								new Edge(pose.get(index), newLine.getVertex(t)));

					}
					this.updateMap(constructedMap, map,
							new Edge(newLine.getVertex(t), edge.getLine()
									.getVertex(edge.getEdgeStart())));
					this.edgeSplit(constructedMap, map, edge,
							edge.getEdgeStart());
				}
			}
		} catch (Exception ex) {
			logger.log(Level.SEVERE, ex.toString());
			System.out.println("***************************");
			System.out.println(ex);
			System.out.println("***************************");
			throw new RuntimeException(ex);
		}
		return 1;
	}

	public List<PoseFile> readAllFiles(File folder, boolean hasAltitude) {
		return PoseFile.readFolder(folder, hasAltitude);
	}

	/**
	 * Constructs map from poses and returns string representation of the map.
	 */

	public List<Vertex> constructMapMain(List<PoseFile> poseFiles, double eps,
			double altEps) {

		List<Vertex> constructedMap = new ArrayList<Vertex>();
		// map contains mapping between vertex keys and their indices in
		// constructedMap
		Map<String, Integer> map = new HashMap<String, Integer>();
		try {
			double length = 0;

// 			System.out.print("1 - ");
			// generate list of files in the folder to process
			for (int k = 0; k < poseFiles.size(); k++) {

				Long startTime = System.currentTimeMillis();
				MapConstruction.curveid = k;
				MapConstruction.curveName = poseFiles.get(k).getCurveName();

// 				System.out.print("2 - ");

				length += poseFiles.get(k).getLength();

				if (poseFiles.get(k).getPose().size() < 2) {
					continue;
				}

				List<Edge> edges = new ArrayList<Edge>();

				/*
				 * siblingMap contains map of key and sibling edges, sibling
				 * edges are line segments between two vertices but going in
				 * opposite direction.
				 */
				Map<String, ArrayList<Edge>> siblingMap = new HashMap<String, ArrayList<Edge>>();

				for (int i = 0; i < constructedMap.size(); i++) {
					Vertex v = constructedMap.get(i);
// 					System.out.print("3 - ");
					for (int j = 0; j < v.getDegree(); j++) {
// 					    System.out.print("4 - ");
						Vertex v1 = constructedMap.get(v
								.getAdjacentElementAt(j));
// 						System.out.print("5 - ");
						if (!v.equals(v1)) {
							Edge newEdge = new Edge(v, v1);
							edges.add(newEdge);
							updateSiblingHashMap(siblingMap, newEdge);
						}
// 						System.out.print("6 - ");
					}
				}
//                 System.out.print("7 - ");
// 				System.out.println(InstrumentationAgent.getObjectSize(constructedMap));
				int result = this.mapConstruction(constructedMap, edges, map,
						poseFiles.get(k).getPose(), eps, altEps);
                                if (result == 0){
                                    continue;
                                }
// 				System.out.println("8");
				this.commitEdgeSplitsAll(constructedMap, map, siblingMap, edges);

				logger.info("k :" + k + " " + MapConstruction.curveName + " "
						+ length + " :"
						+ (System.currentTimeMillis() - startTime) / 60000.00);

			}
		} catch (Exception e) {
                    throw e;
                }
		return constructedMap;
	}

	public static void main(String args[]) {
		MapConstruction mapConstruction = new MapConstruction();

		// path to the folder that contains input tracks.
		String inputPath = args[0];

		// path to the folder where the output will be written.
		String outputpath = args[1];

		// epsilon; see the paper for detail
		double eps = Double.parseDouble(args[2]);

		// if the input files contains altitude information
		boolean hasAltitude = Boolean.parseBoolean(args[3]);

		// minimum altitude difference between two streets.
		double altEps;
		if (args.length > 4) {
			altEps = Double.parseDouble(args[4]);
		} else {
			altEps = 4.0;
		}

		System.out.println(inputPath);
		List<Vertex> constructedMap = mapConstruction.constructMapMain(
				mapConstruction.readAllFiles(new File(inputPath), hasAltitude),
				eps, altEps);
		MapConstruction.writeToFile(constructedMap, outputpath);
	}
}
