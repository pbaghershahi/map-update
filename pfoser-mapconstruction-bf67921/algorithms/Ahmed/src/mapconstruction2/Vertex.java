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


import java.util.ArrayList;
import java.util.List;

public class Vertex {

  private double x; // x coordinate(meters) after Mercator projection
  private double y; // y coordinate(meters) after Mercator projection
  private double z; // z coordinate(meters), it represents altitude
  private double lat; // latitude in WGS84
  private double lng; // longitude in WGS84
  private double alt; // altitude in meters

  /**
   * Contains the indices of adjacent vertices.
   */
  private List<Integer> adjacencyList;

  private boolean done = false;

  /**
   * Timestamp in milliseconds, this field is used when a pose is represented as a list of vertices.
   */
  private String timestamp = "";

  // TODO(Mahmuda): Better to have static factory methods instead of constructor overloading.

  public Vertex() {
    this.adjacencyList = new ArrayList<Integer>();
    this.done = false;
  }

  public Vertex(double x, double y, double z) {
    this();
    this.x = x;
    this.y = y;
    this.z = z;
  }

  public Vertex(double x, double y, double z, String timestamp) {
    this(x, y, z);
    this.timestamp = timestamp;
  }

  public Vertex(double lat, double lng, double alt, double x, double y, double z) {
    this(x, y, z);
    this.lat = lat;
    this.lng = lng;
    this.alt = alt;
  }

  public Vertex(double lat,
      double lng,
      double alt,
      double x,
      double y,
      double z,
      String timestamp) {
    this(lat, lng, alt, x, y, z);
    this.timestamp = timestamp;
  }

  public double getX() {
    return this.x;
  }

  public double getY() {
    return this.y;
  }

  public double getZ() {
    return this.z;
  }

  public double getLat() {
    return this.lat;
  }

  public double getLng() {
    return this.lng;
  }

  public double getAlt() {
    return this.alt;
  }

  public double norm(){
	return Math.sqrt(Math.pow(x, 2)+Math.pow(y, 2)+Math.pow(z, 2));  
  }
  public static double dotProd(Vertex vector1, Vertex vector2){
	  return vector1.getX()*vector2.getX()+vector1.getY()*vector2.getY()+vector1.getZ()*vector2.getZ();
  } 
  public int getDegree() {
    return this.adjacencyList.size();
  }

  public boolean getDone() {
    return this.done;
  }

  public String getTimestamp() {
    return this.timestamp;
  }


  public void setDone(boolean done) {
    this.done = done;
  }

  public List<Integer> getAdjacencyList() {
    return this.adjacencyList;
  }

  /**
   * Adds an element to its adjacency list.
   *
   * @param v is the value to be added in adjacency list
   */
  void addElementAdjList(int v) {
    for (int i = 0; i < this.getDegree(); i++) {
      if (this.adjacencyList.get(i).intValue() == v) {
        return;
      }
    }

    this.adjacencyList.add(v);
  }

  /**
   * Returns the index of a vertex in the adjacency list.
   *
   * @param v the vertex we are looking for
   *
   * @return an int, the index of vertex k if found or -1 otherwise
   */
  public int getIndexAdjacent(int v) {
    return this.adjacencyList.indexOf(v);
  }

  /**
   * Returns the value in the adjacency list at index k
   *
   * @param k the index
   *
   * @return an int, the value at index k or -1 otherwise
   */

  public int getAdjacentElementAt(int k) {
    return this.adjacencyList.get(k).intValue();
  }

  /**
   * Set the adjacent vertex as value at index
   *
   * @param index the index to update
   *
   * @param value the new value at index
   */

  public void setAdjacentElementAt(int index, int value) {
    this.adjacencyList.remove(index);
    this.adjacencyList.add(index, value);
  }

  /**
   * Computes distance between two vertices.
   *
   * @param v2 the vertex with which we should compute distance from this vertex
   *
   * @return a double value which is the distance
   */

  public double dist(Vertex v2) {
    return Math.sqrt(Math.pow(this.x - v2.x, 2) + Math.pow(this.y - v2.y, 2));
  }

  /**
   * Resets a vertex's processing state.
   */

  public void reset() {
    done = false;
  }

  @Override
  public String toString() {
    return String.format("%f %f %f", this.x, this.y, this.z);
  }

  /**
   * @return a deep copy of this vertex
   */
  public Vertex deepCopy() {
    Vertex vertex =
        new Vertex(this.lat, this.lng, this.alt, this.x, this.y, this.z, this.timestamp);
    vertex.done = this.done;

    for (int i = 0; i < this.adjacencyList.size(); i++) {
      vertex.adjacencyList.add(this.adjacencyList.get(i).intValue());
    }
    return vertex;
  }

}