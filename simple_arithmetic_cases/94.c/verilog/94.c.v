module top (
    input wire selector,
    input wire clk,
    input wire rst,
    output reg [12:0] j,
    output reg [12:0] k,
    output reg [12:0] i,
    output reg [12:0] n
);



    always@(posedge clk) begin
        $display("i: %b, j: %b, k: %b, n: %b", i, j, k, n);
    end 
    
    always @(posedge clk) begin
        if(rst)begin
            k <= 80;
            j <= 0;
            i <= 0;
            n <= 100;
        end
        else begin
            if(( i<= n))begin
                    i<= i + 1;
                    j<= j + i;
                    k<= k;
                    n<=n;
                
            end
            else begin
                n <= n;
                j<=j;
                k<=k;
                i<=i;
            end
        end

    end
    // assert property (!((i>n)&&(n*2>=k+j+i)));
endmodule